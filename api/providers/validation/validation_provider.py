"""
Provide validation of an incoming order, borrows
some exception classes and validation methods from the
deprecated validictory library (which this is meant to replace).

We now use the jsonschema library to perform initial validation using
our request_schema (from BaseValidationSchema).  We then define and call
several custom methods to perform further order validation.

A ValidationException is raised if any errors are encountered in the order.

"""

from decimal import Decimal
import copy
import yaml
import os
import math
from collections import Mapping
from addict import Dict
import jsonschema
from api import ValidationException
import api.providers.ordering.ordering_provider as ordering
from api.providers.validation.validation_schema import BaseValidationSchema
from api.providers.validation import MultipleValidationError, SchemaError
import api.domain.sensor as sn
from api import __location__


class ValidationProvider(object):
    """
    Provide custom order validation checks
    """
    def __init__(self):
        self.validator   = None
        self.data_source = None
        self.username    = None
        self.sensors     = ()
        self._errors     = []
        self._itemcount  = 0
        self.restricted  = Dict()
        self.schema      = Dict()

    def validate(self, data_source, username, schema=None):
        self._errors     = []
        self._itemcount  = 0
        self.username    = username
        self.data_source = Dict(data_source)
        self.sensors     = self.selected_sensors()
        self.restricted  = self.yaml_to_dict()

        if not schema:
            self.schema = Dict(BaseValidationSchema.request_schema)
        else:
            self.schema = Dict(schema)
        self.validator = jsonschema.validators.validator_for(self.schema)

        try:
            self.validation_steps()
        except MultipleValidationError as e:
            message, = e.args
            raise ValidationException(msg=message)
        except SchemaError as e:
            message, = e.args
            msg = f"Schema errors:\n{message}"
            raise ValidationException(msg=msg)

        return self.massage_formatting(self.data_source).to_dict()

    @staticmethod
    def yaml_to_dict(path=__location__, filename='domain/restricted.yaml'):
        with open(os.path.join(path, filename), 'r') as f:
            r = Dict(yaml.safe_load(f))
        return r

    def selected_sensors(self):
        """Determine which sensors are present in the order"""
        return set(self.data_source.keys()) & set(sn.SensorCONST.instances.keys())

    def validation_steps(self):
        # perform validation of order structure and contents using our base schema
        self.validator = self.validator(self.schema)
        validation_errors = [e for e in self.validator.iter_errors(self.data_source)]
        for err in validation_errors:
            msg = self.custom_message(err)
            if msg:
                self._errors.append(msg)

        # Iterate over the sensor-types in the order to validate the sensor-specific product restrictions
        for sensor in self.sensors:
            self.validate_restricted(x=self.data_source[sensor],
                                     fieldname='products',
                                     path='{}.products'.format(sensor),
                                     restricted=self.schema.properties[sensor].properties.products.restricted)

        # go through our custom validators to verify the order meets specific criteria
        self.validate_oneormoreobjects()  # make sure at least one sensor was selected
        self.validate_single_obj()        # make sure only one option is selected when appropriate
        self.validate_pixel_units()       # validate the proper units selection based on a projection
        self.validate_extents()           # validate that the image extent makes sense
        self.validate_itemcount()         # validate that the number of inputs in the order does not exceed max value
        self.validate_ps_rng(units='dd')      # validate the decimal degrees value for resize if present
        self.validate_ps_rng(units='meters')  # validate the meters value for resize if present
        self.validate_stats()             # validate a request for stats has valid products

        if self._errors:
            raise MultipleValidationError(errors=self._errors)

    @staticmethod
    def custom_message(error):
        """reformat json schema error messages"""
        try:
            if error.validator == "maxItems":
                msg = "Single sensor input count exceeds maximum of {value} in {path}"
                msg = msg.format(value=error.validator_value,
                                 path='.'.join([str(m) for m in error.path]))
            elif error.validator == "minItems":
                msg = "Property {path} requires at least {value} item(s)"
                msg = msg.format(path='.'.join([str(m) for m in error.path]),
                                 value=error.validator_value)
            elif error.validator == "pattern":
                msg = 'Unrecognized ID "{value}" does not match {pattern} in {path}'
                msg = msg.format(value=error.instance,
                                 pattern=error.validator_value,
                                 path='.'.join([str(m) for m in list(error.path)[:-1]]))
            elif error.validator == "enum":
                if 'products' not in error.path:  # handled by validate_restricted
                    msg = "Unrecognized value '{value}' in {path} - Allowed values: {keys}"
                    msg = msg.format(value=error.instance,
                                     path='.'.join([m for m in error.path if isinstance(m, str)]),
                                     keys=error.validator_value)
                else:
                    msg = None
            elif error.validator == "required":
                msg = 'Required field "{value}" is missing'
                msg = msg.format(value=error.path[-1])

            elif error.validator == "additionalProperties":
                msg = error.message
            elif error.validator == "dependencies":
                msg = error.message
            else:
                msg = "{message} in {path}"
                msg = msg.format(message=error.message, path='.'.join([str(m) for m in error.path]))
        except Exception:
            raise SchemaError
        return msg

    @staticmethod
    def validate_type_object(val):
        return isinstance(val, Mapping) or (hasattr(val, 'keys') and hasattr(val, 'items'))

    @staticmethod
    def validate_type_integer(val):
        return type(val) in (int,)

    @staticmethod
    def validate_type_string(val):
        return isinstance(val, str)

    @staticmethod
    def validate_type_number(val):
        return type(val) in (int, float, Decimal,)

    @staticmethod
    def validate_type_array(val):
        return isinstance(val, (list, tuple))

    @staticmethod
    def calc_extent(xmax, ymax, xmin, ymin, extent_units, resize_units, resize_pixel):
        """Calculate a good estimate of the number of pixels contained
         in an extent"""
        xdif = 0
        ydif = 0

        if extent_units == 'dd' and xmin > 170 and -170 > xmax:
            xdif = 360 - xmin + xmax
        elif xmax > xmin:
            xdif = xmax - xmin

        if ymax > ymin:
            ydif = ymax - ymin

        # This assumes that the only two valid unit options are
        # decimal degrees and meters
        if resize_units != extent_units:
            if extent_units == 'dd':
                resize_pixel /= 111317.254174397
            else:
                resize_pixel *= 111317.254174397

        return int(xdif * ydif / resize_pixel ** 2)

    def verify_extents_dd_and_utm(self, order):
        errors = []
        north_south = [abs(o) for o in [order.image_extents['north'], order.image_extents['south']]]
        if max(north_south) < 80:
            cdict = dict(inzone=order.projection.utm['zone'],
                         east=order.image_extents['east'],
                         west=order.image_extents['west'],
                         zbuffer=3)
            if not self.is_utm_zone_nearby(**cdict):
                msg = ('image_extents (East: {east}, West: {west}) are not near the'
                       ' requested UTM zone ({inzone})'
                       .format(**cdict))
                errors.append(msg)
        return errors

    @staticmethod
    def is_utm_zone_nearby(inzone, east, west, zbuffer=3):
        def long2utm(dd_lon):
            return (math.floor((dd_lon + 180) / 6.) % 60) + 1

        return (long2utm(west) - zbuffer) <= inzone <= (long2utm(east) + zbuffer)

    def validate_oneormoreobjects(self):
        """validate that at least one sensor is present in the list"""
        if not self.sensors:
            msg = 'No requests for products were submitted'
            self._errors.append(msg)

    def validate_pixel_units(self):
        """Validates that the coordinate system output units match as required for the projection (+units=m)"""
        if not self.data_source.projection:
            return
        if not self.validate_type_object(self.data_source.projection):
            return
        if 'image_extents' in self.data_source:
            proj = list(self.data_source.projection.keys()).pop(0)
            valid_cs_units = self.schema.properties.projection.properties[proj].pixel_units
            if not self.validate_type_object(self.data_source.image_extents):
                return
            if 'units' not in self.data_source.image_extents:
                return
            if str(self.data_source.image_extents.units) not in valid_cs_units:
                msg = ('image_extents units must be in "{}" for projection "{}", not "{}"'
                       .format(valid_cs_units, proj, self.data_source.image_extents.units))
                self._errors.append(msg)
                return

    def validate_extents(self, pixel_count=None):
        if 'resize' not in self.data_source and 'image_extents' not in self.data_source:
            return
        # make sure the order contains at least one sensor-type
        if not self.sensors:
            return

        if not pixel_count:
            pixel_count = self.schema.pixel_count

        calc_args = Dict()
        calc_args.xmax = None
        calc_args.ymax = None
        calc_args.xmin = None
        calc_args.ymin = None
        calc_args.extent_units = None
        calc_args.resize_units = None
        calc_args.resize_pixel = None

        # Potential sources that would affect the extent calculations
        if 'projection' in self.data_source:
            if not self.validate_type_object(self.data_source.projection):
                return
            if 'image_extents' in self.data_source:
                if not self.validate_type_object(self.data_source.image_extents):
                    return
                if 'units' not in self.data_source.image_extents:
                    return

        if 'resize' in self.data_source:
            if not self.validate_type_object(self.data_source.resize):
                return
            if set(self.data_source.resize.keys()).symmetric_difference(
                    {'pixel_size_units', 'pixel_size'}):
                return
            if not self.validate_type_string(self.data_source.resize.pixel_size_units):
                return
            if not self.validate_type_number(self.data_source.resize.pixel_size):
                return
            if self.data_source.resize.pixel_size <= 0:
                return

            calc_args.resize_pixel = self.data_source.resize.pixel_size
            calc_args.resize_units = self.data_source.resize.pixel_size_units

        if 'image_extents' in self.data_source:
            if not self.validate_type_object(self.data_source.image_extents):
                return
            if set(self.data_source.image_extents.keys()).symmetric_difference(
                    {'north', 'south', 'east', 'west', 'units'}):
                return
            if 'projection' not in self.data_source or not self.validate_type_object(self.data_source.projection):
                return
            if not self.validate_type_number(self.data_source.image_extents['east']):
                return
            if not self.validate_type_number(self.data_source.image_extents['north']):
                return
            if not self.validate_type_number(self.data_source.image_extents['west']):
                return
            if not self.validate_type_number(self.data_source.image_extents['south']):
                return
            if not self.validate_type_string(self.data_source.image_extents.units):
                return

            calc_args.xmax = self.data_source.image_extents.east
            calc_args.ymax = self.data_source.image_extents.north
            calc_args.xmin = self.data_source.image_extents.west
            calc_args.ymin = self.data_source.image_extents.south
            calc_args.extent_units = self.data_source.image_extents.units

        # If any of the calc_args are None, then we need to input some default values
        # based on the requested inputs
        count_ls = []
        if None in calc_args.values():
            for sensor, sensor_info in sn.SensorCONST.instances.items():
                if sensor in self.data_source and 'inputs' in self.data_source[sensor]:
                    sensor_obj = sensor_info[1]
                    def_res = sensor_obj.default_resolution_m
                    def_xmax = sensor_obj.default_cols * def_res
                    def_ymax = sensor_obj.default_rows * def_res

                    # image_extents or resize is missing, can't be both at this stage
                    # which means we need to substitute default values in
                    if calc_args['resize_pixel'] is None:
                        count_ls.append(self.calc_extent(calc_args.xmax, calc_args.ymax,
                                                         calc_args.xmin, calc_args.ymin,
                                                         calc_args.extent_units, 'meters',
                                                         def_res))
                    if calc_args['xmax'] is None:
                        count_ls.append(self.calc_extent(def_xmax, def_ymax, 0, 0, 'meters',
                                                         calc_args.resize_units,
                                                         calc_args.resize_pixel))
        else:
            count_ls.append(self.calc_extent(**calc_args))

        cmax = max(count_ls)
        cmin = min(count_ls)
        if cmax > pixel_count:
            msg = ('pixel count is greater than maximum size of {}'
                   ' pixels'.format(pixel_count))
            self._errors.append(msg)
        elif cmin < 1:
            msg = ('pixel count value falls below acceptable threshold'
                   ' of 1 pixel')
            self._errors.append(msg)

        # Restrict Pixel-Size in decimal degrees for Geographic Projection only, else Meters
        if 'projection' in self.data_source and 'resize' in self.data_source:
            valid_units = 'meters'
            if 'lonlat' in self.data_source.projection:
                valid_units = 'dd'
            if self.data_source.resize.pixel_size_units != valid_units:
                msg = ('resize units must be in "{}" for projection "{}"'
                       .format(valid_units,
                               list(self.data_source.projection.keys())[0]))
                self._errors.append(msg)

        if 'image_extents' in self.data_source and 'projection' in self.data_source:
            # Validate UTM zone matches image_extents
            #   East/West: Zone Buffer 3 UTM zones (abs(Lat) < 80)
            if self.validate_type_object(self.data_source.projection.get('utm')):
                if not self.validate_type_integer(self.data_source.projection.utm.zone):
                    return
                if not self.validate_type_string(self.data_source.projection.utm.zone_ns):
                    return
                if self.data_source.image_extents.units != 'dd':
                    return
                utm_extents_errors = self.verify_extents_dd_and_utm(self.data_source)
                if utm_extents_errors:
                    self._errors.extend(utm_extents_errors)

    def validate_single_obj(self):
        """Validates that only one dictionary object was passed in"""
        for fieldname in self.data_source:
            value = self.data_source.get(fieldname)
            if isinstance(value, dict):
                schema = self.schema['properties'][fieldname]
                if schema.get('single_obj'):
                    single = True
                else:
                    single = False
                if single:
                    check = len(value)
                    if check > 1:
                        msg = f'{fieldname} field only accepts one object, not {check}'
                        self._errors.append(msg)

    def validate_itemcount(self):
        """
        Make sure the order does not exceed the maximum number of units
        across all sensors
        """
        max_items = self.schema.max_items
        if not self.sensors:
            return
        for sensor in self.sensors:
            if not self.validate_type_object(self.data_source[sensor]):
                continue
            vals = self.data_source[sensor]['inputs']
            if not self.validate_type_array(vals):
                continue
            self._itemcount += len(vals)
            if self._itemcount > max_items:
                msg = ('Order exceeds maximum allowable inputs of {max}'
                       .format(max=max_items))
                self._errors.append(msg)
                return

    def validate_ps_rng(self, units):
        """Validates that the pixel size for given units falls within a preset range"""
        __units__ = {'dd': 'Decimal Degrees', 'meters': 'Meters'}
        if not self.data_source['resize']:
            return
        if not self.validate_type_object(self.data_source['resize']):
            return
        if self.data_source['resize']['pixel_size_units'] not in \
                self.schema.properties.resize.properties.pixel_size_units.enum:
            # This would get caught by the jsonschema enum validator
            return
        if units != self.data_source['resize']['pixel_size_units']:
            # Only validate the single unit type
            return
        value = self.data_source['resize']['pixel_size']
        if self.validate_type_number(value):
            _min, _max = self.schema.properties.resize.properties.pixel_size[f'ps_{units}_rng']
            if not _min <= value <= _max:
                msg = 'Value of {value} for {path} must fall between {_min} and {_max} {units}'
                msg = msg.format(value=value,
                                 path='resize.pixel_size',
                                 _min=_min,
                                 _max=_max,
                                 units=__units__[units])
                self._errors.append(msg)

    def validate_stats(self, stats_included=False):
        """
        Validate that requests for stats are accompanied by logical products
        """
        # if stats not enabled, or not requesting stats, return
        if not self.sensors:
            return
        for sensor in self.sensors:
            if not self.validate_type_object(self.data_source[sensor]):
                continue
            if 'stats' in self.data_source[sensor]['products']:
                stats_included = True
                break
        if not stats_included:
            return
        if 'plot_statistics' not in self.data_source:
            return
        if not self.data_source.plot_statistics:  # == False
            return

        stats = self.restricted.stats

        for sensor in self.sensors:
            _sensor = sensor.replace('_collection', '')
            if _sensor not in stats.sensors:
                continue
            if self.validate_type_object(self.data_source[sensor]) and self.data_source[sensor]['products']:
                if not set(stats.products) & set(self.data_source[sensor].products):
                    msg = "You must request valid products for statistics: {}"
                    msg = msg.format(stats.products)
                    self._errors.append(msg)
            else:
                msg = "Required field 'products' missing"
                self._errors.append(msg)

    def validate_restricted(self, x, fieldname, path, restricted):
        """
        Validate that the requested products are available by date or role

        Args:
            x (addict.Dict): A portion of the order for a specific sensor
            fieldname (str): The schema property being validated (really just "products")
            path (str): Path of the schema property being validated
            restricted (bool): A property from schema.properties.<sensor>.properties.products
        """
        if not restricted:
            return
        # Like extents, we need to do some initial validation of the input up front,
        # and let those individual validators output the errors
        if not self.validate_type_object(x):
            return
        if not x.inputs:
            return
        if not self.validate_type_array(x.inputs):
            return

        req_prods = x[fieldname]

        if not req_prods:
            return

        try:
            req_scene = x.inputs[0]
        except IndexError:
            return

        inst = sn.instance(req_scene)

        avail_prods = (ordering.OrderingProvider()
                       .available_products(x['inputs'], self.username))

        not_implemented = avail_prods.pop('not_implemented', None)
        date_restricted = avail_prods.pop('date_restricted', None)
        ordering_restricted = avail_prods.pop('ordering_restricted', None)

        # Check for to make sure there is only one sensor type in there
        if len(avail_prods) > 1:
            return

        if not_implemented:
            self._errors.append("Requested IDs are not recognized. Remove: {}"
                                .format(not_implemented))

        if date_restricted:
            restr_prods = list(date_restricted.keys())

            for key in restr_prods:
                if key not in req_prods:
                    date_restricted.pop(key, None)

            if date_restricted:
                for product_type in date_restricted:
                    msg = ("Requested {} products are restricted by date. "
                           "Remove {} scenes: {}"
                           .format(product_type, path.split('.products')[0],
                                   [p.upper() for p in date_restricted[product_type]]))
                    self._errors.append(msg)

        if ordering_restricted:
            restr_sensors = ordering_restricted.keys()

            for sensor in restr_sensors:
                msg = ("Requested sensor is restricted from ordering. "
                       "Remove: {}".format(sensor))
                self._errors.append(msg)

        prods = []
        for key in avail_prods:
            prods = [_ for _ in avail_prods[key]['products']]

        if not prods:
            return

        dif = list(set(req_prods) - set(prods))

        if date_restricted:
            for d in dif:
                if d in date_restricted:
                    dif.remove(d)

        if dif:
            for d in dif:
                if self.validate_type_object(x):
                    msg = "Remove invalid product request '{prod}' in {sensor}.products - Available products: {avail}"
                    msg = msg.format(prod=d,
                                     sensor=path.split('.products')[0],
                                     avail=prods)
                    self._errors.append(msg)

        # Enforce non-customized l1 ordering restriction for Landsat
        restr_source = self.restricted['source']
        landsat_sensors = restr_source['sensors']
        sensors = [s for s in self.data_source.keys() if s in sn.SensorCONST.instances.keys() and
                   s in landsat_sensors]

        def parse_customize(c):
            return (c in self.data_source) and (self.data_source.get(c) != restr_source.get(c))

        if sensors and 'LANDSAT' in inst.lta_json_name:
            if not set(req_prods) - set(restr_source['products']):
                if not any([parse_customize(s) for s in restr_source['custom']]):
                    msg = restr_source['message'].strip()
                    if msg not in self._errors:
                        self._errors.append(msg)

        # Enforce non-customized l1 ordering restriction for MODIS and VIIRS
        restr_modis_viirs = self.restricted['source_daac']
        modis_viirs_sensors = restr_modis_viirs['sensors']
        sensors_mv = [s for s in self.data_source.keys() if s in sn.SensorCONST.instances.keys()
                      and s in modis_viirs_sensors]

        def parse_modis_customize(c):
            return (c in self.data_source) and (self.data_source.get(c) != restr_modis_viirs.get(c))

        if sensors_mv and ('MODIS' in inst.lta_json_name or 'VIIRS' in inst.lta_json_name):
            if not set(req_prods) - set(restr_modis_viirs['products']):
                if not any([parse_modis_customize(z) for z in restr_modis_viirs['custom']]):
                    msg = restr_modis_viirs['message'].strip()
                    if msg not in self._errors:
                        self._errors.append(msg)

        # Enforce restricted product ordering for MODIS NDVI
        if 'MODIS' in inst.lta_json_name:
            restr_modis_ndvi = self.restricted['source_modis_ndvi']
            modis_sensors = restr_modis_ndvi['modis_sensors']
            req_ndvi_sensors = [s for s in self.data_source.keys() if s in sn.SensorCONST.instances.keys()
                                and s in modis_sensors]
            invalid_req = set(req_ndvi_sensors) - set(restr_modis_ndvi['ndvi_sensors'])
            if invalid_req:
                if 'modis_ndvi' in req_prods:
                    msg = restr_modis_ndvi['message'].strip()
                    if msg not in self._errors:
                        self._errors.append(msg)

        # Enforce sensor-restricted product ordering for LaORCA (but only if user has access to this product)
        if 'aq_refl' in req_prods and 'aq_refl' in prods:
            restr_aq_refl_info = self.restricted['source_aq_refl_sensors']
            aq_refl_sensors = restr_aq_refl_info['all_sensors']
            req_aq_refl_sensors = [s for s in self.data_source.keys() if s in sn.SensorCONST.instances.keys()
                                   and s in aq_refl_sensors]
            invalid_aq_refl_req = set(req_aq_refl_sensors) - set(restr_aq_refl_info['valid_sensors'])
            if invalid_aq_refl_req:
                msg = restr_aq_refl_info['message'].strip()
                if msg not in self._errors:
                    self._errors.append(msg)

        # Make sure that all required st options are included (but only if user has access to this product)
        if 'st' in prods:
            stalg_single_channel = 'stalg_single_channel'
            stalg_split_window = 'stalg_split_window'
            reanalysis_data = ['reanalsrc_narr', 'reanalsrc_merra2', 'reanalsrc_fp', 'reanalsrc_fpit']
            if 'st' in req_prods:
                if stalg_single_channel not in req_prods and stalg_split_window not in req_prods:
                    msg = "Missing surface temperature algorithm - " \
                          "please choose from ['{0}' (olitirs only), '{1}']".format(stalg_split_window,
                                                                                    stalg_single_channel)
                    if msg not in self._errors:
                        self._errors.append(msg)
                if stalg_single_channel in req_prods and not any([r for r in reanalysis_data if r in req_prods]):
                    msg = "Missing reanalysis data source for single channel algorithm - " \
                          "please choose from {}".format(reanalysis_data)
                    if msg not in self._errors:
                        self._errors.append(msg)

            all_st_options = list()
            all_st_options.append(stalg_split_window)
            all_st_options.append(stalg_single_channel)
            all_st_options.extend(reanalysis_data)
            if any([x for x in all_st_options if x in req_prods]) and 'st' not in req_prods:
                msg = "Must include 'st' in products if specifying surface temperature options"
                if msg not in self._errors:
                    self._errors.append(msg)

    @staticmethod
    def massage_formatting(order):
        """
        To avoid complications down the line, we need to ensure proper case formatting
        on the order, while still being somewhat case agnostic

        We also need to add 'stats' product to all the sensors if 'plot_statistics'
        was set to True

        :param order: incoming order after validation
        :return: order with the inputs reformatted
        """
        prod_keys = sn.SensorCONST.instances.keys()

        stats = False
        if 'plot_statistics' in order and order['plot_statistics']:
            stats = True

        for key in order:
            if key in prod_keys:
                item1 = order[key]['inputs'][0]

                prod = sn.instance(item1)
                if isinstance(prod, sn.Landsat):
                    order[key]['inputs'] = [s.upper() for s in order[key]['inputs']]
                elif isinstance(prod, sn.Modis):
                    order[key]['inputs'] = ['.'.join([p[0].upper(),
                                                      p[1].upper(),
                                                      p[2].lower(),
                                                      p[3],
                                                      p[4]]) for p in [s.split('.') for s in order[key]['inputs']]]

                elif isinstance(prod, sn.Viirs):
                    order[key]['inputs'] = ['.'.join([p[0].upper(),
                                                      p[1].upper(),
                                                      p[2].lower(),
                                                      p[3],
                                                      p[4]]) for p in [s.split('.') for s in order[key]['inputs']]]

                elif isinstance(prod, sn.Sentinel2_AB):
                    order[key]['inputs'] = [s.upper() for s in order[key]['inputs']]

                if stats:
                    if 'stats' not in order[key]['products']:
                        order[key]['products'].append('stats')

        return order

    def fetch_projections(self):
        """
        Pass along projection information
        :return: dict
        """
        schema = BaseValidationSchema
        return copy.deepcopy(schema.valid_params['projections'])

    def fetch_formats(self):
        """
        Pass along valid file formats
        :return: dict
        """
        schema = BaseValidationSchema
        return copy.deepcopy(schema.valid_params['formats'])

    def fetch_resampling(self):
        """
        Pass along valid resampling options
        :return: dict
        """
        schema = BaseValidationSchema
        return copy.deepcopy(schema.valid_params['resampling_methods'])

    def fetch_order_schema(self):
        """
        Pass along the schema used for validation
        :return: dict
        """
        schema = BaseValidationSchema
        return copy.deepcopy(schema.request_schema)

    @staticmethod
    def fetch_product_types():
        """
        Pass along the values/readable-names for product-types
        :return: dict
        """
        return sn.ProductNames().groups()

    __call__ = validate
