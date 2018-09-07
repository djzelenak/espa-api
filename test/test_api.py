#!/usr/bin/env python
import unittest
import yaml
import copy

from api.interfaces.ordering.version1 import API as APIv1
from api.util import lowercase_all
from api.util.dbconnect import db_instance
import version0_testorders as testorders
from api.providers.validation.validictory import BaseValidationSchema
from api import ValidationException, InventoryException, __location__

import os
from api.domain.mocks.order import MockOrder
from api.domain.mocks.user import MockUser
from api.domain.order import Order
from api.domain.user import User
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.providers.production.mocks.production_provider import MockProductionProvider
from api.providers.production.production_provider import ProductionProvider
from api.external.mocks import lta as mocklta
from api.external.mocks import inventory as mockinventory
from api.system.logger import ilogger as logger
from mock import patch

api = APIv1()
production_provider = ProductionProvider()
mock_production_provider = MockProductionProvider()
cfg = ConfigurationProvider()


class TestAPI(unittest.TestCase):
    def setUp(self):
        logger.warning('Testing API started...')
        os.environ['espa_api_testing'] = 'True'
        # create a user
        self.mock_user = MockUser()
        self.mock_order = MockOrder()
        user_id = self.mock_user.add_testing_user()
        order_id = self.mock_order.generate_testing_order(user_id)
        self.order = Order.find(order_id)
        self.user = User.find(user_id)
        self.product_id = 'LT05_L1TP_032028_20120425_20160830_01_T1'
        self.sensor_id = 'tm5_collection'
        self.staff_product_id = 'LE07_L1TP_010028_20050420_20160925_01_T1'
        self.staff_sensor = 'etm7_collection'
        self.global_product_id = 'LE07_L1TP_026027_20170912_20171008_01_T1'

        staff_user_id = self.mock_user.add_testing_user()
        self.staff_user = User.find(staff_user_id)
        self.staff_user.update('is_staff', True)
        staff_order_id = self.mock_order.generate_testing_order(staff_user_id)
        staff_order = Order.find(staff_order_id)
        staff_scene = staff_order.scenes()[0]
        staff_scene.update('name', self.staff_product_id)
        user_scene = self.order.scenes()[0]
        user_scene.update('name', self.staff_product_id)

        with open(os.path.join(__location__, 'domain/restricted.yaml')) as f:
            self.restricted = yaml.load(f.read())
            self.restricted['all']['role'].remove('restricted_prod')

    def tearDown(self):
        logger.warning('Testing API done.')
        # clean up orders
        self.mock_order.tear_down_testing_orders()
        # clean up users
        self.mock_user.cleanup()
        os.environ['espa_api_testing'] = ''

    def test_api_versions_key_val(self):
        self.assertEqual(set(api.api_versions().keys()), set(['v0', 'v1']))

    def test_get_available_products_key_val(self):
        self.assertEqual(api.available_products(self.product_id, self.user.username).keys()[0], self.sensor_id)

    def test_get_available_products_by_staff(self):
        # staff should see all available products
        self.user.update('is_staff', True)
        return_dict = api.available_products(self.staff_product_id, self.staff_user.username)
        for item in self.restricted['all']['role']:
            self.assertTrue(item in return_dict[self.staff_sensor]['products'])

    def test_get_available_products_by_public(self):
        # public should not see products listed in api/domain.restricted.yaml
        self.user.update('is_staff', False)
        return_dict = api.available_products(self.staff_product_id, self.user.username)
        for item in self.restricted['all']['role']:
            self.assertFalse(item in return_dict[self.staff_sensor]['products'])

    def test_fetch_user_orders_by_email_val(self):
        orders = api.fetch_user_orders(email=self.user.email)
        self.assertTrue(len(orders) > 1)
        self.assertIn(self.order.orderid, [o.orderid for o in orders])

    def test_fetch_user_orders_by_username_val(self):
        orders = api.fetch_user_orders(username=self.user.username)
        self.assertTrue(len(orders) > 1)
        self.assertIn(self.order.orderid, [o.orderid for o in orders])

    def test_fetch_order_by_orderid_val(self):
        order = api.fetch_order(self.order.orderid)
        self.assertEqual(1, len(order))
        self.assertEqual(order[0].orderid, self.order.orderid)

    def test_fetch_order_by_orderid_invalid(self):
        invalid_orderid = 'invalidorderid'
        response = api.fetch_order(invalid_orderid)
        self.assertEqual(response, list())

    def test_fetch_item_status_valid(self):
        response = api.item_status(self.order.orderid)
        self.assertEqual(set(response), {self.order.orderid})
        self.assertIsInstance(response[self.order.orderid], list)
        self.assertEqual(set([s.name for s in self.order.scenes()]),
                         set([s.name for s in response[self.order.orderid]]))


class TestValidation(unittest.TestCase):
    def setUp(self):
        logger.warning('Testing Validation started...')
        os.environ['espa_api_testing'] = 'True'

        self.mock_user = MockUser()
        self.staffuser = User.find(self.mock_user.add_testing_user())
        self.staffuser.update('is_staff', True)

        self.base_order = lowercase_all(testorders.build_base_order())
        self.base_schema = BaseValidationSchema.request_schema

    def test_validation_get_order_schema(self):
        """
        Make sure the ordering schema is retrievable as a dict
        """
        self.assertIsInstance(api.validation.fetch_order_schema(), dict)

    def test_validation_get_valid_formats(self):
        """
        Make sure the file format options are retrievable as a dict
        """
        self.assertIsInstance(api.validation.fetch_formats(), dict)

    def test_validation_get_valid_resampling(self):
        """
        Make sure the resampling options are retrievable as a dict
        """
        self.assertIsInstance(api.validation.fetch_resampling(), dict)

    def test_validation_get_valid_projections(self):
        """
        Make sure the projection options are retrievable as a dict
        """
        self.assertIsInstance(api.validation.fetch_projections(), dict)

    def test_validate_good_order(self):
        """
        Test a series of known good orders
        """
        for proj in testorders.good_test_projections:
            valid_order = copy.deepcopy(self.base_order)
            valid_order['projection'] = {proj: testorders.good_test_projections[proj]}
            if 'lonlat' not in valid_order['projection']:
                valid_order['resize'] = {"pixel_size": 30, "pixel_size_units": "meters"}

            try:
                good = api.validation(valid_order, self.staffuser.username)
            except ValidationException as e:
                self.fail('Raised ValidationException: {}'.format(e.message))

    def test_modis_resize(self):
        """
        Most common issue of orders resizing MODIS to 30m pixels, without setting the extents
        """
        modis_order = {'mod09a1': {'inputs': ['mod09a1.a2016305.h11v04.006.2016314200836'],
                                   'products': ['l1']},
                       'resampling_method': 'cc',
                       'resize': {'pixel_size': 30,
                                  'pixel_size_units': 'meters'},
                       'format': 'gtiff'}

        exc = 'pixel count is greater than maximum size of'
        exc_key = '1 validation errors'

        try:
            api.validation(modis_order, self.staffuser.username)
        except Exception as e:
            self.assertIn(exc_key, e.response)
            self.assertIsInstance(e.response[exc_key], list)
            self.assertIn(exc, str(e.response[exc_key]))
        else:
            self.fail('Failed MODIS pixel resize test')

    def test_validate_bad_orders(self):
        """
        Build a series of invalid orders to try and catch any potential errors in a
        submitted order

        Check to make sure the invalid order raises ValidationException, then check
        the exception message for the expected error message

        The abbreviated flag for the InvalidOrders class changes the number of invalid
        orders that will get tested.

        abbreviated=True - test each constraint type once
        abbreviated=False - test each constraint on each value location in the nested structure
        """
        exc_type = ValidationException
        invalid_order = copy.deepcopy(self.base_order)

        for proj in testorders.good_test_projections:
            invalid_order['projection'] = {proj: testorders.good_test_projections[proj]}

            invalid_list = testorders.InvalidOrders(invalid_order, self.base_schema, abbreviated=False)

            for order, test, exc in invalid_list:
                # empty lists cause assertRaisesRegExp to fail
                exc = str(exc).replace('[', '\[')
                with self.assertRaisesRegexp(exc_type, exc):
                    api.validation(order, self.staffuser.username)

    def test_validate_sr_restricted_human_readable(self):
        """
        Assert that a human readable response is returned for unavailable or date restricted products
        """
        exc_type = ValidationException
        invalid_list = {'olitirs8_collection': {'inputs': ['lc08_l1tp_031043_20160225_20170224_01_t1'],
                                     'products': ['sr'],
                                     'err_msg': 'Requested {} products are restricted by date'},
                        'oli8_collection': {'inputs': ['lo08_l1tp_021049_20150304_20170227_01_t1'],
                                 'products': ['sr'],
                                 'err_msg': 'Requested {} products are not available'}}

        for stype in invalid_list:
            invalid_order = copy.deepcopy(self.base_order)
            invalid_order[stype]['inputs'] = invalid_list[stype]['inputs']
            invalid_order[stype]['products'] = invalid_list[stype]['products']
            for p in invalid_order[stype]['products']:
                err_message = invalid_list[stype]['err_msg'].format(p)
                with self.assertRaisesRegexp(exc_type, err_message):
                    api.validation.validate(invalid_order, self.staffuser.username)

    def test_projection_units_geographic(self):
        """
        Make sure Geographic (latlon) projection only accepts "dd" units
        """
        part_order = {
            "olitirs8_collection": {
                "inputs": ['lc08_l1tp_015035_20140713_20170304_01_t1'],
                "products": ["l1"]
            },
            "projection": {"lonlat": None},
            "format": "gtiff",
            "resampling_method": "cc"
            }
        bad_parts = {
            "resize": {"pixel_size": 30, "pixel_size_units": "meters"},
            "image_extents": {"north": 80, "south": -80,
                              "east": 170, "west": -170, "units": "meters"},
            }

        err_msg = '{} units must be in "dd" for projection "lonlat"'
        exc_type = ValidationException

        for bname in bad_parts:
            invalid_order = copy.deepcopy(part_order)
            invalid_order.update({bname: bad_parts.get(bname)})
            with self.assertRaisesRegexp(exc_type, err_msg.format(bname)):
                api.validation.validate(invalid_order, self.staffuser.username)

    def test_l1_only_restricted(self):
        """ Landsat Level-1 data needs to go through other channels """
        invalid_order = {
            "olitirs8_collection": {
                "inputs": ["lc08_l1tp_015035_20140713_20170304_01_t1"],
                "products": ["l1"]
            },
            "format": "gtiff"
        }
        with self.assertRaisesRegexp(ValidationException, 'Landsat Level-1 data products'):
            api.validation.validate(invalid_order, self.staffuser.username)

    def test_l1_only_restricted_override(self):
        """ Customizations or other sensors should override Level-1 restrictions """
        valid_orders = [{
            "olitirs8_collection": {
                "inputs": ["lc08_l1tp_015035_20140713_20170304_01_t1"],
                "products": ["l1"]
            },
            "format": "envi"
            },
            {
            "olitirs8_collection": {
                "inputs": ["lc08_l1tp_015035_20140713_20170304_01_t1"],
                "products": ["l1"]
            },
            "myd13a2": {
                "inputs": ["myd13a2.a2017249.h19v06.006.2017265235022"],
                "products": ["l1"]
            },
            "format": "gtiff"
        }]
        for vorder in valid_orders:
            api.validation.validate(vorder, self.staffuser.username)

    # def test_validate_utm_zone(self):
    #     invalid_order = copy.deepcopy(self.base_order)
    #     invalid_order['projection'] = {'utm': {'zone': 50, 'zone_ns': 'north'}}
    #     invalid_order['image_extents'] = {'east': 32.5, 'north': 114.9, 'south': 113.5, 'units': u'dd', 'west': 31.5}
    #     with self.assertRaisesRegexp(ValidationException, 'are not near the requested UTM zone'):
    #         api.validation.validate(invalid_order, self.staffuser.username)


class TestInventory(unittest.TestCase):
    def setUp(self):
        logger.warning('Testing Inventory started...')
        os.environ['espa_api_testing'] = 'True'
        self.lta_prod_good = u'LE07_L1TP_026027_20170912_20171008_01_T1'
        self.lta_prod_bad = u'LE07_L1TP_026027_20170912_20171008_01_T1'
        self.lpdaac_prod_good = u'MOD09A1.A2016305.h11v04.006.2016314200836'
        self.lpdaac_prod_bad = u'MOD09A1.A2016305.h11v04.006.9999999999999'

        self.lta_order_good = {'etm7_collection': {'inputs': [self.lta_prod_good]}}
        self.lta_order_bad = {'olitirs8_collection': {'inputs': [self.lta_prod_bad]}}

        self.lpdaac_order_good = {'mod09a1': {'inputs': [self.lpdaac_prod_good]}}
        self.lpdaac_order_bad = {'mod09a1': {'inputs': [self.lpdaac_prod_bad]}}


    # @patch('api.external.lta.requests.post', mocklta.get_verify_scenes_response)
    # @patch('api.external.lta.check_lta_available', lambda: True)
    # def test_lta_good(self):
    #     """
    #     Check LTA support from the inventory provider
    #     """
    #     self.assertIsNone(api.inventory.check(self.lta_order_good))

#    @patch('api.external.inventory.requests.post', mockinventory.CachedRequestPreventionSpoof)
#    @patch('api.external.inventory.available', lambda: True)
#    @patch('api.external.inventory.get_cached_session', mockinventory.get_cached_session)
#    @patch('api.external.inventory.LTACachedService.get_lookup', mockinventory.get_cache_values)
#    def test_lta_good(self):
#        """
#        Check LTA support from the inventory provider
#        """
#        cfg.put('system.m2m_val_enabled', 'True')
#        self.assertIsNone(api.inventory.check(self.lta_order_good))
#        cfg.put('system.m2m_val_enabled', 'False')
#
#    @patch('api.external.lta.requests.post', mocklta.get_verify_scenes_response_invalid)
#    @patch('api.external.lta.check_lta_available', lambda: True)
#    def test_lta_bad(self):
#        """
#        Check LTA support from the inventory provider
#        """
#        with self.assertRaises(InventoryException):
#            api.inventory.check(self.lta_order_bad)
#
    @patch('api.external.lpdaac.LPDAACService.input_exists', lambda x, y: True)
    @patch('api.external.lpdaac.LPDAACService.check_lpdaac_available', lambda y: True)
    def test_lpdaac_good(self):
        """
        Check LPDAAC support from the inventory provider
        """
        self.assertIsNone(api.inventory.check(self.lpdaac_order_good))

    @patch('api.external.lpdaac.LPDAACService.input_exists', lambda x, y: False)
    @patch('api.external.lpdaac.LPDAACService.check_lpdaac_available', lambda y: True)
    def test_lpdaac_bad(self):
        """
        Check LPDAAC support from the inventory provider
        """
        with self.assertRaises(InventoryException):
            api.inventory.check(self.lpdaac_order_bad)

