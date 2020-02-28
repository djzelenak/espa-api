
import copy
import jsonschema
import collections
from test.version0_testorders import build_base_order, good_test_projections

BASE_ORDER = build_base_order()
PROJECTIONS = good_test_projections


class InvalidOrders(object):
    """
    Build a list of invalid orders and the expected validation errors based
    on a given schema
    """
    def __init__(self, valid_order, schema, alt_fields=None, abbreviated=False):
        self.valid_order     = valid_order
        self.schema          = schema
        self.validator       = jsonschema.validators.validator_for(self.schema)
        self.validator       = self.validator(self.schema)
        self.alt_fields      = alt_fields
        self.abbreviated     = abbreviated
        self.abbr            = []
        self.invalid_list    = []
        self.invalid_list    .extend(self.build_invalid_list())
        self.invalid_list    .extend(self.invalidate_dependencies())

    def __iter__(self):
        return iter(self.invalid_list)

    def build_invalid_list(self, path=None):
        """
        Recursively move through the base order and the validation schema

        """
        if not path:
            path = tuple()

        results = []

        sch_base = self.schema
        base = self.valid_order

        for key in path:
            sch_base = sch_base['properties'][key]
            base = base[key]

        if not path and 'oneormoreobjects' in sch_base:
            results.extend(self.invalidate_oneormoreobjects(self.schema['oneormoreobjects'], path))

        for key, val in base.items():
            constraints = sch_base['properties'][key]
            mapping = path + (key,)

            for constr_type, constr in constraints.items():
                if self.abbreviated and constr_type in self.abbr:
                    continue
                elif self.abbreviated:
                    self.abbr.append(constr_type)

                invalidatorname = f"invalidate_{constr_type}"

                try:
                    invalidator = getattr(self, invalidatorname, None)
                except Exception:
                    raise Exception('{} has no associated testing'.format(constr_type))

                if not invalidator:
                    raise Exception('{} has no associated testing'.format(constr_type))

                results.extend(invalidator(constr, mapping))

            if constraints['type'] == 'object':
                results.extend(self.build_invalid_list(mapping))

        return results

    def invalidate_oneormoreobjects(self, keys, mapping):
        """
        Remove any matching keys, so that nothing matches
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        for key in keys:
            order = self.delete_key_loc(order, mapping + (key,))

        msg = "No requests for products were submitted"
        results.append((order, 'oneormoreobjects', msg))

        return results

    def invalidate_dependencies(self):
        """
        Remove dependencies, one at a time
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        dependencies = self.schema['dependencies']

        for p in dependencies:
            dependency = dependencies[p]
            # e.g. image_extents: ['projection']
            for dep in dependency:
                path       = (dep,)
                msg        = "'{dep}' is a dependency of '{p}'"
                msg        = msg.format(dep=dep,
                                        p=p)
                order      = self.delete_key_loc(order, path)
                results    .append((order, 'dependencies', msg))

        return results

    def invalidate_type(self, val_type, mapping):
        """
        Change the variable type
        """
        order = copy.deepcopy(self.valid_order)
        results = []
        test_vals = []

        if val_type == 'string':
            test_vals.append(9999)

        elif val_type == 'integer':
            test_vals.append('NOT A NUMBER')
            test_vals.append(1.1)

        elif val_type == 'number':
            test_vals.append('NOT A NUMBER')

        elif val_type == 'boolean':
            test_vals.append('NOT A BOOL')
            test_vals.append(2)
            test_vals.append(-1)

        elif val_type == 'object':
            test_vals.append('NOT A DICTIONARY')

        elif val_type == 'array':
            test_vals.append('NOT A LIST')

        elif val_type == 'null':
            test_vals.append('NOT NONE')

        elif val_type == 'any':
            pass

        else:
            raise Exception('{} constraint not accounted for in testing'.format(val_type))

        for val in test_vals:
            upd = self.build_update_dict(mapping, val)
            # only use the single quotes around {val} if it's a string
            if type(val) != str:
                msg = "{val} is not of type '{val_type}' in {mapping}"
            else:
                msg = "'{val}' is not of type '{val_type}' in {mapping}"
            msg = msg.format(val=val,
                             val_type=val_type,
                             mapping='.'.join(mapping))
            order = self.update_dict(order, upd)
            results.append((order, 'type', msg))

        return results

    def invalidate_single_obj(self, val_type, mapping):
        """
        This really only applies to the projection field

        append another valid structure
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        if 'lonlat' in order['projection']:
            order['projection'].update({'aea': good_test_projections['aea']})
        else:
            order['projection'].update({'lonlat': good_test_projections['lonlat']})

        msg = "{mapping} field only accepts one object, not {val}"
        msg = msg.format(mapping='.'.join(mapping),
                         val=2)
        results.append((order, 'single_obj', msg))

        return results

    def invalidate_enum(self, enums, mapping):
        """
        Add a value not covered in the enum list

        Example:
            "Unrecognized value 'NOT VALID ENUM' in projection.aea.datum - Allowed values: ['wgs84', 'nad27', 'nad83']"
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        inv = 'NOT VALID ENUM'
        # msg = r"Remove invalid product request '.*' in {mapping} - Available products: {enums}"
        msg = "Unrecognized value '{inv}' in {mapping} - Allowed values: {enums}"
        xsg = "Unrecognized value '{inv}' in {mapping} - Allowed values: {keys}"
        msg = msg.format(inv=inv,
                         mapping='.'.join(mapping),
                         enums=enums)

        upd = self.build_update_dict(mapping, inv)
        results.append((self.update_dict(order, upd), 'enum', msg))
        return results

    def invalidate_required(self, req, mapping):
        """
        If the key is required, remove it
        Missing required property "format"
        """
        order = copy.deepcopy(self.valid_order)
        results = []
        if req:
            msg = f'Required field "{mapping[-1]}" is missing'
            order = self.delete_key_loc(order, mapping)
            results.append((order, 'required', msg))

        return results

    def invalidate_maximum(self, max_val, mapping):
        """
        Add one to the maximum allowed value

        Example:
            91 is greater than the maximum of 90 in projection.aea.standard_parallel_1
        """
        order   = copy.deepcopy(self.valid_order)
        results = []
        val     = max_val + 1
        upd     = self.build_update_dict(mapping, val)

        msg = '{val} is greater than the maximum of {max_val} in {mapping}'
        msg = msg.format(val=val,
                         max_val=max_val,
                         mapping='.'.join(mapping))

        order = self.update_dict(order, upd)
        results.append((order, 'maximum', msg))

        return results

    def invalidate_minimum(self, min_val, mapping):
        """
        Subtract one from the minimum allowed value

        Example:
            -91 is less than the minimum of -90 in projection.aea.standard_parallel_1
        """
        order   = copy.deepcopy(self.valid_order)
        results = []
        val     = min_val - 1
        upd     = self.build_update_dict(mapping, val)

        msg = '{val} is less than the minimum of {min_val} in {mapping}'
        msg = msg.format(val=val,
                         min_val=min_val,
                         mapping='.'.join(mapping))

        order = self.update_dict(order, upd)
        results.append((order, 'minimum', msg))

        return results

    def invalidate_uniqueItems(self, unique, mapping):
        """
        Add a duplicate entry into the list

        Example:
            ['sr', 'stats', 'sr'] has non-unique elements in etm7_collection.products
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        if unique:
            base = order

            for key in mapping:
                base = base[key]

            base.append(base[0])

            upd     = self.build_update_dict(mapping, base)
            msg     = "has non-unique elements in {mapping}"
            msg     = msg.format(mapping='.'.join(mapping))
            order   = self.update_dict(order, upd)

            results.append((order, 'uniqueItems', msg))

        return results

    def invalidate_extents(self, max_pixels, mapping):
        # This is deeply tied into resize options as well
        order = copy.deepcopy(self.valid_order)
        results = []

        ext = {'north': 0,
               'south': 0,
               'east': 0,
               'west': 0,
               'units': 'dd'}

        # max pixels + 1 by keeping one of the dimensions = 1
        dd_ext = {'west': 0,
                  'east': (max_pixels + 1) * 0.0002695,
                  'south': 0,
                  'north': 0.0002695,
                  'units': 'dd'}

        m_ext = {'west': 0,
                 'east': (max_pixels + 1) * 30,
                 'south': 0,
                 'north': 30,
                 'units': 'meters'}

        order.pop('resize')

        if 'lonlat' in order['projection']:
            upd = {'image_extents': {'units': 'meters'}}
            msg = 'resize units must be in "dd" for projection "lonlat"'
            results.append((self.update_dict(order, upd), 'extents', msg))
        else:
            upd = {'image_extents': m_ext}
            msg = 'pixel count is greater than maximum size of {} pixels'.format(max_pixels)
            results.append((self.update_dict(order, upd), 'extents', msg))

        upd = {'image_extents': dd_ext}
        msg = 'pixel count is greater than maximum size {} pixels'.format(max_pixels)
        results.append((self.update_dict(order, upd), 'extents', msg))

        upd = {'image_extents': ext}
        msg = 'pixel count value falls below acceptable threshold of 1 pixel'
        results.append((self.update_dict(order, upd), 'extents', msg))

        return results

    def invalidate_ps_dd_rng(self, rng, mapping):
        """
        Set values outside of the valid range

        Example:
            Value of 0.0001695 for resize.pixel_size must fall between 0.0002695 and 0.0449155 Decimal Degrees
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        test_vals = [rng[0] - 1, rng[1] + 1]

        for val in test_vals:
            upd = self.build_update_dict(mapping[:-1], {'pixel_size': val, 'pixel_size_units': 'dd'})

            msg = "Value of {val} for {mapping} must fall between {min_val} and {max_val} Decimal Degrees"
            msg = msg.format(val=val,
                             mapping='.'.join(mapping),
                             min_val=rng[0],
                             max_val=rng[1])

            results.append((self.update_dict(order, upd), 'ps_dd_rng', msg))

        return results

    def invalidate_ps_meters_rng(self, rng, mapping):
        """
        Set values outside of the valid range

        Example:
            Value of 5001 for resize.pixel_size must fall between 30 and 5000 Meters
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        if 'lonlat' in order['projection']:
            return results

        test_vals = [rng[0] - 1, rng[1] + 1]

        for val in test_vals:
            upd = self.build_update_dict(mapping[:-1], {'pixel_size': val, 'pixel_size_units': 'meters'})

            msg = "Value of {val} for {mapping} must fall between {min_val} and {max_val} Meters"
            msg = msg.format(val=val,
                             mapping='.'.join(mapping),
                             min_val=rng[0],
                             max_val=rng[1])

            results.append((self.update_dict(order, upd), 'ps_meters_rng', msg))

        return results

    def invalidate_stats(self, stats, mapping):
        """
        If stats restrictions are in place, remove valid stats products from order
        """
        order = copy.deepcopy(self.valid_order)
        results = []
        if stats:
            new_order = {}
            for item in order:
                new_order[item] = order[item]
                if isinstance(new_order[item], dict) and 'inputs' in new_order[item].keys():
                    new_order[item]['products'] = ['l1', 'stats']
            try:
                # sentinel does not have an l1 ordering option
                del new_order['sentinel']
            except KeyError:
                pass
            msg = "You must request valid products for statistics"
            results.append((new_order, 'stats_required', msg))

        return results

    def invalidate_maxItems(self, count_key, mapping):
        """
        Increase the number of items in an array to exceed a set maximum

        Example:
            Single sensor input count exceeds maximum of 5000 in tm4_collection.inputs
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        max_val = 0
        # Need to locate the max value setting in the schema
        for key, val in self.schema.items():
            if key == 'max_items' and self.schema[key] == count_key:
                max_val = self.schema[key]
                break

        base = order
        for key in mapping:
            base = base[key]

        base.extend([base[0]] * max_val)

        upd = self.build_update_dict(mapping, base)

        msg = "Single sensor input count exceeds maximum of {max_val} in {mapping}"
        msg = msg.format(max_val=max_val,
                         mapping='.'.join(mapping))

        results.append((self.update_dict(order, upd), 'maxItems', msg))

        return results

    def invalidate_minItems(self, num, mapping):
        """
        Reduce the number of items in the list below the threshold

        Example:
            Property etm7_collection.inputs requires at least 1 item(s)
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        ls = order
        for key in mapping:
            ls = ls[key]

        while len(ls) >= num:
            del ls[-1]

        upd = self.build_update_dict(mapping, ls)

        msg = 'Property {mapping} requires at least {num} item(s)'
        msg = msg.format(mapping='.'.join(mapping),
                         num=num)

        results.append((self.update_dict(order, upd), 'minItems', msg))

        return results

    def invalidate_pixel_units(self, units, mapping):
        """
        Put an invalid projection output into a limited projection (like, geographic)
        """
        order = copy.deepcopy(self.valid_order)
        results = []

        parts = {'resize': 'pixel_size_units',
                 'image_extents': 'units'}

        val = 'meters'
        for p, n in parts.items():
            if p in order and val not in units:
                upd = self.build_update_dict((p, n), 'meters')
                msg = '{object} units must be in "dd" for projection'.format(object=p)
                results.append((self.update_dict(order, upd), p, msg))
        return results

    @staticmethod
    def invalidate_restricted(restr, mapping):
        """
        This should be handled by other tests
        """
        return []

    @staticmethod
    def invalidate_title(old, new):
        # Title is not something we want to check
        return []

    @staticmethod
    def invalidate_display_rank(old, new):
        # display_rank is not something we want to check
        return []

    @staticmethod
    def invalidate_properties(val_type, mapping):
        """
        Tested through other methods
        """
        return []

    @staticmethod
    def invalidate_items(val_type, mapping):
        """
        Should be tested internally by the JSONSchema validator
        Subsets need to be tested through other methods
        """
        return []

    def delete_key_loc(self, old, path):
        """
        Delete a key from a nested dictionary
        """
        ret = copy.deepcopy(old)

        if len(path) > 1:
            ret[path[0]] = self.delete_key_loc(ret[path[0]], path[1:])
        elif len(path) == 1:
            ret.pop(path[0], None)

        return ret

    def build_update_dict(self, path, val):
        """
        Build a new nested dictionary following a series of keys
        with a an endpoint value
        """
        ret = {}

        if len(path) > 1:
            ret[path[0]] = self.build_update_dict(path[1:], val)
        elif len(path) == 1:
            ret[path[0]] = val

        return ret

    def update_dict(self, old, new):
        """
        Update a nested dictionary value following along a defined key path
        """
        ret = copy.deepcopy(old)

        for key, val in new.items():
            if isinstance(val, collections.Mapping):
                ret[key] = self.update_dict(ret[key], val)
            else:
                ret[key] = new[key]
        return ret
