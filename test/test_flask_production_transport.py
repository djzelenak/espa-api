#!/usr/bin/env python

import json
import os
import unittest
from test import version0_testorders as testorders

from api.domain.mocks.order import MockOrder
from api.domain.mocks.user import MockUser
from api.domain.user import User
from api.interfaces.ordering.mocks.version1 import MockAPI
from api.providers.production.mocks.production_provider import MockProductionProvider
from api.transports import http_main
from api.util import lowercase_all
from api.util.dbconnect import db_instance
from mock import patch

api = MockAPI()
production_provider = MockProductionProvider()


class ProductionTransportTestCase(unittest.TestCase):

    def setUp(self):
        os.environ['espa_api_testing'] = 'True'
        # create a user
        self.mock_user = MockUser()
        self.mock_order = MockOrder()
        self.user = User.find(self.mock_user.add_testing_user())
        self.order_id = self.mock_order.generate_testing_order(self.user.id)

        self.app = http_main.app.test_client()
        self.app.testing = True

        self.sceneids = self.mock_order.scene_names_list(self.order_id)[0:2]

        with db_instance() as db:
            uidsql = "select user_id, orderid from ordering_order limit 1;"
            db.select(uidsql)
            self.userid = db[0]['user_id']
            self.orderid = db[0]['orderid']

            itemsql = "select name, order_id from ordering_scene limit 1;"
            db.select(itemsql)
            self.itemid = db[0][0]
            itemorderid = db[0][1]

            ordersql = "select orderid from ordering_order where id = {};".format(itemorderid)
            db.select(ordersql)
            self.itemorderid = db[0][0]

        self.base_order = lowercase_all(testorders.build_base_order())

    def tearDown(self):
        # clean up orders
        self.mock_order.tear_down_testing_orders()
        # clean up users
        self.mock_user.cleanup()
        os.environ['espa_api_testing'] = ''

    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_get_production_api(self):
        response = self.app.get('/production-api', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response.content_type == 'application/json'
        assert set(response_data.keys()) == {'0', '1'}

    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_get_production_api_v1(self):
        response = self.app.get('/production-api/v1', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert set(response_data.keys()) == {"operations", "description"}
        assert "ESPA Production" in response_data['description']

    @patch('api.providers.production.production_provider.ProductionProvider.get_products_to_process',
           production_provider.get_products_to_process_inputs)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_get_production_api_products_modis(self):
        url = "/production-api/v1/products?for_user=bilbo&product_types=modis"
        response = self.app.get(url, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        correct_resp = {'encode_urls': False, 'for_user': 'bilbo',
                        'record_limit': 500, 'product_types': 'modis',
                        'priority': None}
        assert response_data == correct_resp

    @patch('api.providers.production.production_provider.ProductionProvider.get_products_to_process',
           production_provider.get_products_to_process_inputs)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_get_production_api_products_landsat(self):
        url = "/production-api/v1/products?for_user=bilbo&product_types=landsat"
        response = self.app.get(url, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        correct_resp = {'encode_urls': False, 'for_user': 'bilbo',
                        'record_limit': 500, 'product_types': 'landsat',
                        'priority': None}
        assert response_data == correct_resp

    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    @patch('api.providers.production.production_provider.ProductionProvider.update_status',
           production_provider.update_status_inputs)
    def test_post_production_api_update_status(self):
        url = "/production-api/v1/update_status"
        data_dict = {'name': 't10000xyz401', 'orderid': 'kyle@usgs.gov-09222015-123456',
                    'processing_loc': 'update_status', 'status': 'updated'}
        response = self.app.post(url, data=json.dumps(data_dict), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data == data_dict

    @patch('api.providers.production.production_provider.ProductionProvider.set_product_error',
           production_provider.set_product_error_inputs)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_post_production_api_set_product_error(self):
        url = "/production-api/v1/set_product_error"
        data_dict = {'name': 't10000xyz401', 'orderid': 'kyle@usgs.gov-09222015-123456',
                     'processing_loc': 'xyz', 'error': 'oopsie'}
        response = self.app.post(url, data=json.dumps(data_dict), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data == data_dict

    @patch('api.providers.production.production_provider.ProductionProvider.set_product_unavailable',
           production_provider.set_product_unavailable_inputs)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_post_production_api_set_product_unavailable(self):
        url = "/production-api/v1/set_product_unavailable"
        data_dict = {'name': 't10000xyz401', 'orderid': 'kyle@usgs.gov-09222015-123456',
                     'processing_loc': 'xyz', 'error': 'oopsie', 'note': 'them notes'}
        response = self.app.post(url, data=json.dumps(data_dict), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data == data_dict

    @patch('api.providers.production.production_provider.ProductionProvider.mark_product_complete',
           production_provider.set_mark_product_complete_inputs)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_post_production_api_mark_product_complete(self):
        url = "/production-api/v1/mark_product_complete"
        data_dict = {'name': 't10000xyz401', 'orderid': 'kyle@usgs.gov-09222015-123456',
                     'processing_loc': 'xyz',
                     'completed_file_location': '/tmp',
                     'cksum_file_location': '/tmp/txt.txt',
                     'log_file_contents': 'details'}
        response = self.app.post(url, data=json.dumps(data_dict), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data == data_dict

    @patch('api.providers.production.production_provider.ProductionProvider.handle_orders',
           production_provider.respond_true)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_post_production_api_handle_orders(self):
        url = "/production-api/v1/handle-orders"
        response = self.app.get(url, data=json.dumps({}), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data is True

    @patch('api.providers.production.production_provider.ProductionProvider.queue_products',
           production_provider.queue_products_inputs)
    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_post_production_api_queue_products(self):
        url = "/production-api/v1/queue-products"
        data_dict = {'order_name_tuple_list': 'order_name_tuple_list',
                     'processing_location': 'processing_location',
                     'job_name': 'job_name'}
        response = self.app.post(url, data=json.dumps(data_dict), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data == data_dict

    @patch('api.interfaces.production.version1.API.get_production_whitelist', api.get_production_whitelist)
    def test_get_production_api_configurations(self):
        url = "/production-api/v1/configuration/system_message_title"
        response = self.app.get(url, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert list(response_data.keys()) == ['system_message_title']

    @patch('api.interfaces.admin.version1.API.get_stat_whitelist', api.get_stat_whitelist)
    def test_get_production_api_stat_products_complete_24_hrs(self):
        url = "/production-api/v1/statistics/stat_products_complete_24_hrs"
        response = self.app.get(url, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        response_data = json.loads(response.get_data())
        assert response_data == 0
