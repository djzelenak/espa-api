from __future__ import absolute_import
from decimal import Decimal
import copy
import yaml
import re
import os
import math

import validictory
from validictory.validator import RequiredFieldValidationError, SchemaError, DependencyValidationError

from api.providers.validation import ValidationInterfaceV0
from api import ValidationException
import api.providers.ordering.ordering_provider as ordering
import api.domain.sensor as sn

from api import __location__


class OrderValidatorV0(validictory.SchemaValidator):
    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username')
        super(OrderValidatorV0, self).__init__(*args, **kwargs)
        self.data_source = None
        self.base_schema = None
        self._itemcount = None
        with open(os.path.join(__location__, 'domain/restricted.yaml')) as f:
            self.restricted = yaml.load(f.read())

    def validate(self, data, schema):
        self.data_source = data
        self.base_schema = schema
        self._itemcount = {}
        super(OrderValidatorV0, self).validate(data, schema)

    def validate_pixel_units(self, x, fieldname, schema, path, valid_cs_units=('meters',)):
        """Validates that the coordinate system output units match as required for the projection (+units=m)"""
        if fieldname in x:
            if 'image_extents' in self.data_source:
                if not self.validate_type_object(self.data_source['image_extents']):
                    return
                if not 'units' in self.data_source['image_extents']:
                    return
                if self.data_source['image_extents']['units'] not in valid_cs_units:
                    msg = ('image_extents units must be in "{}" for projection "{}", not "{}"'
                           .format(','.join(valid_cs_units), fieldname,
                                   self.data_source['image_extents']['units']))
                    self._errors.append(msg)
                    return

    def validate_extents(self, x, fieldname, schema, path, pixel_count=200000000):
        if 'resize' not in self.data_source and 'image_extents' not in self.data_source:
            return
        if not (set(self.data_source.keys()) & set(sn.SensorCONST.instances.keys())):
            return

        calc_args = {'xmax': None,
                     'ymax': None,
                     'xmin': None,
                     'ymin': None,
                     'extent_units': None,
                     'resize_units': None,
                     'resize_pixel': None}

        # Since we can't predict which validation methods are called
        # first we need to make sure that all the values are present
        # and are of the correct type, let the other built-in
        # validations handle the actual error output for most failures

        # Potential sources that would affect the extent calculations
        if 'projection' in self.data_source:
            if not self.validate_type_object(self.data_source['projection']):
                return
            if 'image_extents' in self.data_source:
                if not self.validate_type_object(self.data_source['image_extents']):
                    return
                if 'units' not in self.data_source['image_extents']:
                    return

        if 'resize' in self.data_source:
            if not self.validate_type_object(self.data_source['resize']):
                return
            if set(self.data_source['resize'].keys()).symmetric_difference(
                    {'pixel_size_units', 'pixel_size'}):
                return
            if not self.validate_type_string(self.data_source['resize']['pixel_size_units']):
                return
            if not self.validate_type_number(self.data_source['resize']['pixel_size']):
                return
            if self.data_source['resize']['pixel_size'] <= 0:
                return

            calc_args['resize_pixel'] = self.data_source['resize']['pixel_size']
            calc_args['resize_units'] = self.data_source['resize']['pixel_size_units']

        if 'image_extents' in self.data_source:
            if not self.validate_type_object(self.data_source['image_extents']):
                return
            if set(self.data_source['image_extents'].keys()).symmetric_difference(
                    {'north', 'south', 'east', 'west', 'units'}):
                return
            if 'projection' not in self.data_source or not self.validate_type_object(self.data_source['projection']):
                return
            if not self.validate_type_number(self.data_source['image_extents']['east']):
                return
            if not self.validate_type_number(self.data_source['image_extents']['north']):
                return
            if not self.validate_type_number(self.data_source['image_extents']['west']):
                return
            if not self.validate_type_number(self.data_source['image_extents']['south']):
                return
            if not self.validate_type_string(self.data_source['image_extents']['units']):
                return

            calc_args['xmax'] = self.data_source['image_extents']['east']
            calc_args['ymax'] = self.data_source['image_extents']['north']
            calc_args['xmin'] = self.data_source['image_extents']['west']
            calc_args['ymin'] = self.data_source['image_extents']['south']
            calc_args['extent_units'] = self.data_source['image_extents']['units']

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
                        count_ls.append(self.calc_extent(calc_args['xmax'], calc_args['ymax'],
                                                         calc_args['xmin'], calc_args['ymin'],
                                                         calc_args['extent_units'], 'meters',
                                                         def_res))
                    if calc_args['xmax'] is None:
                        count_ls.append(self.calc_extent(def_xmax, def_ymax, 0, 0, 'meters',
                                                         calc_args['resize_units'],
                                                         calc_args['resize_pixel']))
        else:
            count_ls.append(self.calc_extent(**calc_args))

        cmax = max(count_ls)
        cmin = min(count_ls)
        if cmax > pixel_count:
            msg = ('{}:{} pixel count is greater than maximum size of {}'
                   ' pixels'.format(path, fieldname, pixel_count))
            self._errors.append(msg)
        elif cmin < 1:
            msg = ('{}:{} pixel count value falls below acceptable threshold'
                   ' of 1 pixel'.format(path, fieldname))
            self._errors.append(msg)

        # Restrict Pixel-Size in decimal degrees for Geographic Projection only, else Meters
        if 'projection' in self.data_source and 'resize' in self.data_source:
            valid_units = 'meters'
            if 'lonlat' in self.data_source['projection']:
                valid_units = 'dd'
            if self.data_source['resize']['pixel_size_units'] != valid_units:
                msg = ('resize units must be in "{}" for projection "{}"'
                       .format(valid_units,
                               self.data_source['projection'].keys()[0]))
                self._errors.append(msg)

        if 'image_extents' in self.data_source and 'projection' in self.data_source:
            # Validate UTM zone matches image_extents
            #   East/West: Zone Buffer 3 UTM zones (abs(Lat) < 80)
            if self.validate_type_object(self.data_source['projection'].get('utm')):
                if not self.validate_type_integer(self.data_source['projection']['utm'].get('zone')):
                    return
                if not self.validate_type_string(self.data_source['projection']['utm'].get('zone_ns')):
                    return
                if self.data_source['image_extents']['units'] != 'dd':
                    return
                utm_extents_errors = self.verify_extents_dd_and_utm(self.data_source)
                if utm_extents_errors:
                    self._errors.extend(utm_extents_errors)

    def verify_extents_dd_and_utm(self, order):
        errors = []
        if max(map(abs, [order['image_extents']['north'],
                            order['image_extents']['south']])) < 80:
            cdict = dict(inzone=order['projection']['utm']['zone'],
                        east=order['image_extents']['east'],
                        west=order['image_extents']['west'],
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

    @staticmethod
    def calc_extent(xmax, ymax, xmin, ymin, extent_units, resize_units, resize_pixel):
        """Calculate a good estimate of the number of pixels contained
         in an extent"""
        max_count = 0

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

    def validate_single_obj(self, x, fieldname, schema, path, single=False):
        """Validates that only one dictionary object was passed in"""
        value = x.get(fieldname)

        if isinstance(value, dict):
            if single:
                if len(value) > 1:
                    msg = ('{} field only accepts one object, not {}'
                           .format(path, len(value)))
                    self._errors.append(msg)

    def validate_enum(self, x, fieldname, schema, path, options=None):
        '''
        Validates that the value of the field is equal to one of the specified option values
        '''
        value = x.get(fieldname)
        if value is not None:
            if callable(options):
                options = options(x)
            if value not in options:
                if not (value == '' and schema.get('blank', self.blank_by_default)):
                    msg = ("Not available: {} products for {}. "
                           "Please choose from available products: {}"
                           .format(value, path.split('.products')[0], options))
                    self._errors.append(msg)

    def validate_pattern(self, x, fieldname, schema, path, pattern=None):
        '''
        Validates that the given field, if a string, matches the given regular expression.
        '''
        value = x.get(fieldname)
        if (isinstance(value, basestring) and
            (isinstance(pattern, basestring) and not re.match(pattern, value)
             or not isinstance(pattern, basestring) and not pattern.match(value))):
                self._errors.append("Remove unrecognized input ID: {} ({} must match regex {})"
                                    .format(value.upper(), path.split('.inputs')[0], pattern))


    def validate_enum_keys(self, x, fieldname, schema, path, valid_list):
        """Validates the keys in the given object match expected keys"""
        value = x.get(fieldname)

        if value is not None:

            if not hasattr(value, '__iter__'):
                value = [value]

            for field in value:
                if field not in valid_list:
                    msg = ('Unknown key {}: Allowed keys {}'.format(field, valid_list))
                    self._errors.append(msg)

    def validate_abs_rng(self, x, fieldname, schema, path, val_range):
        """Validates that the absolute value of a field falls within a given range"""
        value = x.get(fieldname)

        if isinstance(value, (int, long, float, Decimal)):
            if not val_range[0] <= abs(value) <= val_range[1]:
                msg = ('Absolute value of {} must fall between {} and {}'
                       .format(path, val_range[0], val_range[1]))
                self._errors.append(msg)

    def validate_ps_dd_rng(self, x, fieldname, schema, path, val_range):
        """Validates the pixel size given for Decimal Degrees is within a given range"""
        value = x.get(fieldname)

        if isinstance(value, (int, long, float, Decimal)):
            if 'pixel_size_units' in x:
                if x['pixel_size_units'] == 'dd':
                    if not val_range[0] <= value <= val_range[1]:
                        msg = ('Value of {} must fall between {} and {} decimal degrees'
                               .format(path, val_range[0], val_range[1]))
                        self._errors.append(msg)

    def validate_ps_meters_rng(self, x, fieldname, schema, path, val_range):
        """Validates the pixel size given for Meters is within a given range"""
        value = x.get(fieldname)

        if isinstance(value, (int, long, float, Decimal)):
            if 'pixel_size_units' in x:
                if x['pixel_size_units'] == 'meters':
                    if not val_range[0] <= value <= val_range[1]:
                        msg = ('Value of {} must fall between {} and {} meters'
                               .format(path, val_range[0], val_range[1]))
                        self._errors.append(msg)

    def validate_stats(self, x, fieldname, schema, path, stats):
        """
        Validate that requests for stats are accompanied by logical products
        """
        # if stats not enabled, or not requesting stats, return
        if not stats:
            return

        if 'plot_statistics' not in self.data_source:
            return

        if self.data_source['plot_statistics'] is False:
            return

        # path resembles '<obj>.olitirs8.products'
        stats = self.restricted['stats']
        sensor = path.split('.')[1].replace('_collection', '')
        if sensor not in stats['sensors']:
            return

        if x.get('products'):
            if not set(stats['products']) & set(x['products']):
                msg = ('You must request valid products for statistics: {}'
                       .format(stats['products']))
                self._errors.append(msg)
        else:
            msg = "Required field 'products' missing"
            self._errors.append(msg)

    def validate_restricted(self, x, fieldname, schema, path, restricted):
        """Validate that the requested products are available by date or role"""
        if not restricted:
            return

        # Like extents, we need to do some initial validation of the input up front,
        # and let those individual validators output the errors
        if 'inputs' not in x:
            return
        if not self.validate_type_array(x['inputs']):
            return

        req_prods = x.get(fieldname)

        if not req_prods:
            return

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
            restr_prods = date_restricted.keys()

            for key in restr_prods:
                if key not in req_prods:
                    date_restricted.pop(key, None)

            if date_restricted:
                for product_type in date_restricted:
                    msg = ("Requested {} products are restricted by date. "
                           "Remove {} scenes: {}"
                           .format(product_type, path.split('.products')[0],
                                   [x.upper()
                                    for x in date_restricted[product_type]]))
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
                if type(x) == dict:
                    scene_ids = [s.upper() for s in x['inputs']]
                    msg = ("Requested {} products are not available. "
                           "Remove {} scenes: {}"
                           .format(d, path.split('.products')[0], scene_ids))
                    self._errors.append(msg)

        restr_source = self.restricted['source']
        sensors = [s for s in self.data_source.keys() if s in sn.SensorCONST.instances.keys()]
        other_sensors = set(sensors) - set(restr_source['sensors'])
        parse_customize = lambda c: ((c in self.data_source) and
                                     (self.data_source.get(c) != restr_source.get(c)))
        if not other_sensors:
            if not set(req_prods) - set(restr_source['products']):
                if not any(map(parse_customize, restr_source['custom'])):
                    msg = restr_source['message'].strip()
                    if msg not in self._errors:
                        self._errors.append(msg)


    def validate_oneormoreobjects(self, x, fieldname, schema, path, key_list):
        """Validates that at least one value is present from the list"""
        val = x.get(fieldname)

        if self.validate_type_object(val):
            for key in key_list:
                if key in val:
                    return

            msg = 'No requests for products were submitted'
            self._errors.append(msg)

    def validate_set_ItemCount(self, x, fieldname, schema, path, (key, val)):
        """Sets item count limits for multiple arrays across a potential order"""
        if key in self._itemcount:
            raise SchemaError('ItemCount {} set multiple times'.format(key))
        if not self.validate_type_integer(val):
            raise SchemaError('Max value for {} must be an integer'.format(key))

        self._itemcount[key] = {'count': 0, 'max': val}

    def validate_ItemCount(self, x, fieldname, schema, path, key):
        """
        Increment the count for the specified key

        Make sure the total count for the category does not exceed a max value
        """
        vals = x.get(fieldname)

        if not self.validate_type_array(vals):
            return

        self._itemcount[key]['count'] += len(vals)

        if self._itemcount[key]['count'] > self._itemcount[key]['max']:
            msg = ('Count exceeds size limit of {max} for {key}'
                   .format(max=self._itemcount[key]['max'], key=key))
            self._errors.append(msg)


class BaseValidationSchema(object):
    formats = {'gtiff':    'GeoTiff',
               'envi':     'ENVI',
               'hdf-eos2': 'HDF-EOS2',
               'netcdf':   'NetCDF'}

    resampling_methods = {'nn':  'Nearest Neighbor',
                          'bil': 'Bilinear Interpolation',
                          'cc':  'Cubic Convolution'}

    projections = {'aea': {'type': 'object',
                           'title': 'Albers Equal Area',
                           'pixel_units':  ('meters', 'dd'),
                           'display_rank': 0,
                           'properties': {'standard_parallel_1': {'type': 'number',
                                                                  'title': '1st Standard Parallel',
                                                                  'display_rank': 2,
                                                                  'required': True,
                                                                  'minimum': -90,
                                                                  'maximum': 90},
                                          'standard_parallel_2': {'type': 'number',
                                                                  'title': '2nd Standard Parallel',
                                                                  'display_rank': 3,
                                                                  'required': True,
                                                                  'minimum': -90,
                                                                  'maximum': 90},
                                          'central_meridian': {'type': 'number',
                                                               'title': 'Central Meridian',
                                                               'display_rank': 1,
                                                               'required': True,
                                                               'minimum': -180,
                                                               'maximum': 180},
                                          'latitude_of_origin': {'type': 'number',
                                                                 'title': 'Latitude of Origin',
                                                                 'display_rank': 0,
                                                                 'required': True,
                                                                 'minimum': -90,
                                                                 'maximum': 90},
                                          'false_easting': {'type': 'number',
                                                            'title': 'False Easting (meters)',
                                                            'display_rank': 4,
                                                            'required': True},
                                          'false_northing': {'type': 'number',
                                                             'title': 'False Northing (meters)',
                                                             'display_rank': 5,
                                                             'required': True},
                                          'datum': {'type': 'string',
                                                    'title': 'Datum',
                                                    'required': True,
                                                    'display_rank': 6,
                                                    'enum': {'wgs84': 'World Geodetic System 1984',
                                                             'nad27': 'North American Datum 1927',
                                                             'nad83': 'North American Datum 1983'}}}},
                   'utm': {'type': 'object',
                           'pixel_units':  ('meters', 'dd'),
                           'display_rank': 1,
                           'title': 'Universal Transverse Mercator',
                           'properties': {'zone': {'type': 'integer',
                                                   'title': 'UTM Grid Zone Number',
                                                   'display_rank': 0,
                                                   'required': True,
                                                   'minimum': 1,
                                                   'maximum': 60},
                                          'zone_ns': {'type': 'string',
                                                      'title': 'UTM Hemisphere',
                                                      'display_rank': 1,
                                                      'required': True,
                                                      'enum': {'north': 'North', 'south': 'South'}}}},
                   'lonlat': {'type': 'null',
                              'pixel_units': ('dd',),
                              'title': 'Geographic',
                              'display_rank': 2},
                   'sinu': {'type': 'object',
                            'title': 'Sinusoidal',
                            'pixel_units': ('meters', 'dd'),
                            'display_rank': 3,
                            'properties': {'central_meridian': {'type': 'number',
                                                                'title': 'Central Meridian',
                                                                'display_rank': 0,
                                                                'required': True,
                                                                'minimum': -180,
                                                                'maximum': 180},
                                           'false_easting': {'type': 'number',
                                                             'title': 'False Easting (meters)',
                                                             'display_rank': 1,
                                                             'required': True},
                                           'false_northing': {'type': 'number',
                                                              'title': 'False Northing (meters)',
                                                              'display_rank': 2,
                                                              'required': True}}},
                   'ps': {'type': 'object',
                          'title': 'Polar Stereographic',
                          'pixel_units': ('meters', 'dd'),
                          'display_rank': 4,
                          'properties': {'longitudinal_pole': {'type': 'number',
                                                               'title': 'Longitudinal Pole',
                                                               'display_rank': 0,
                                                               'required': True,
                                                               'minimum': -180,
                                                               'maximum': 180},
                                         'latitude_true_scale': {'type': 'number',
                                                                 'title': 'Latitude True Scale',
                                                                 'display_rank': 1,
                                                                 'required': True,
                                                                 'abs_rng': (60, 90)},
                                         'false_easting': {'type': 'number',
                                                           'title': 'False Easting (meters)',
                                                           'display_rank': 2,
                                                           'required': True},
                                         'false_northing': {'type': 'number',
                                                            'title': 'False Northing (meters)',
                                                            'display_rank': 3,
                                                            'required': True}}}}

    extents = {'north': {'type': 'number',
                         'title': 'Upper left Y coordinate',
                         'display_rank': 2,
                         'required': True},
               'south': {'type': 'number',
                         'title': 'Lower right Y coordinate',
                         'display_rank': 4,
                         'required': True},
               'east': {'type': 'number',
                        'title': 'Lower right X coordinate',
                        'display_rank': 3,
                        'required': True},
               'west': {'type': 'number',
                        'title': 'Upper left X coordinate',
                        'display_rank': 1,
                        'required': True},
               'units': {'type': 'string',
                         'title': 'Coordinate system units',
                         'display_rank': 0,
                         'required': True,
                         'enum': {'dd': 'Decimal Degrees', 'meters': 'Meters'}}}

    resize = {'pixel_size': {'type': 'number',
                             'title': 'Pixel Size',
                             'display_rank': 0,
                             'required': True,
                             'ps_dd_rng': (0.0002695, 0.0449155),
                             'ps_meters_rng': (30, 5000)},
              'pixel_size_units': {'type': 'string',
                                   'title': 'Pixel Size Units',
                                   'display_rank': 1,
                                   'required': True,
                                   'enum': {'dd': 'Decimal Degrees', 'meters': 'Meters'}}}

    request_schema = {'type': 'object',
                      'set_ItemCount': ('inputs', 5000),
                      'extents': 200000000,
                      'properties': {'projection': {'properties': projections,
                                                    'type': 'object',
                                                    'title': 'Reproject Products',
                                                    'display_rank': 1,
                                                    'single_obj': True},
                                     'image_extents': {'type': 'object',
                                                       'title': 'Modify Image Extents',
                                                       'display_rank': 2,
                                                       'properties': extents,
                                                       'dependencies': ['projection']},
                                     'format': {'type': 'string',
                                                'title': 'Output Format',
                                                'display_rank': 0,
                                                'required': True,
                                                'enum': formats},
                                     'resize': {'type': 'object',
                                                'title': 'Pixel Resizing',
                                                'display_rank': 3,
                                                'properties': resize},
                                     'resampling_method': {'type': 'string',
                                                           'title': 'Resample Method',
                                                           'display_rank': 4,
                                                           'enum': resampling_methods},
                                     'plot_statistics': {'type': 'boolean',
                                                         'title': 'Plot Output Product Statistics'},
                                     'note': {'type': 'string',
                                              'title': 'Order Description (optional)',
                                              'required': False,
                                              'blank': True}}}

    _sensor_reg = sn.SensorCONST.instances
    sensor_schema = {}
    for key in _sensor_reg:
        sensor_schema[key] = {'type': 'object',
                              'properties': {'inputs': {'type': 'array',
                                                        'required': True,
                                                        'ItemCount': 'inputs',
                                                        'uniqueItems': True,
                                                        'minItems': 1,
                                                        'items': {'type': 'string',
                                                                  'pattern': _sensor_reg[key][0]}},
                                             'products': {'type': 'array',
                                                          'uniqueItems': True,
                                                          'required': True,
                                                          'restricted': True,
                                                          'stats': True,
                                                          'minItems': 1,
                                                          'items': {'type': 'string',
                                                                    'enum': sn.instance(
                                                                            _sensor_reg[key][2]).products}}}}

    request_schema['properties'].update(sensor_schema)
    request_schema['oneormoreobjects'] = sensor_schema.keys()

    valid_params = {'formats': {'formats': formats},
                    'resampling_methods': {'resampling_methods': resampling_methods},
                    'projections': projections}


class ValidationProvider(ValidationInterfaceV0):
    schema = BaseValidationSchema

    def validate(self, order, username):
        """
        Validate an incoming order to make sure everything is kosher

        :param order: incoming order dict
        :param username: username associated with the order
        :return: validated order
        """
        order = copy.deepcopy(order)
        try:
            v = OrderValidatorV0(format_validators=None, required_by_default=False, blank_by_default=False,
                                 disallow_unknown_properties=True, apply_default_to_data=False,
                                 fail_fast=False, remove_unknown_properties=False, username=username)

            v.validate(order, self.schema.request_schema)
            # validictory.validate(order, self.schema.request_schema, fail_fast=False, disallow_unknown_properties=True,
            #                      validator_cls=OrderValidatorV0, required_by_default=False)
        except validictory.MultipleValidationError as e:
            raise ValidationException(e.message)
        except validictory.SchemaError as e:
            message = 'Schema errors:\n' + e.message
            raise ValidationException(message)

        return self.massage_formatting(order)

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

                if stats:
                    if 'stats' not in order[key]['products']:
                        order[key]['products'].append('stats')

        return order

    def fetch_projections(self):
        """
        Pass along projection information
        :return: dict
        """
        return copy.deepcopy(self.schema.valid_params['projections'])

    def fetch_formats(self):
        """
        Pass along valid file formats
        :return: dict
        """
        return copy.deepcopy(self.schema.valid_params['formats'])

    def fetch_resampling(self):
        """
        Pass along valid resampling options
        :return: dict
        """
        return copy.deepcopy(self.schema.valid_params['resampling_methods'])

    def fetch_order_schema(self):
        """
        Pass along the schema used for validation
        :return: dict
        """
        return copy.deepcopy(self.schema.request_schema)

    def fetch_product_types(self):
        """
        Pass along the values/readable-names for product-types
        :return: dict
        """
        return sn.ProductNames().groups()


    __call__ = validate
