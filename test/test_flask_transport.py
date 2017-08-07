#!/usr/bin/env python

import os
import json
import unittest
import base64

import version0_testorders as testorders

from mock import patch

from api.transports import http
from api.util import lowercase_all
from api.util.dbconnect import db_instance
from api.domain.user import User
from api.domain.mocks.order import MockOrder
from api.domain.mocks.user import MockUser

from api.interfaces.ordering.mocks.version1 import MockAPI

mock_api = MockAPI()


class TransportTestCase(unittest.TestCase):

    def setUp(self):
        os.environ['espa_api_testing'] = 'True'
        # create a user
        self.mock_user = MockUser()
        self.mock_order = MockOrder()
        self.user = User.find(self.mock_user.add_testing_user())
        self.order_id = self.mock_order.generate_testing_order(self.user.id)

        self.app = http.app.test_client()
        self.app.testing = True

        self.sceneids = self.mock_order.scene_names_list(self.order_id)[0:2]

        token = ':'.join((self.user.username, 'foo'))
        auth_string = "Basic {}".format(base64.b64encode(token))
        self.headers = {"Authorization": auth_string}

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
        self.sensors = [k for k in self.base_order.keys() if isinstance(self.base_order[k], dict) and 'inputs' in self.base_order[k]]
        self.inputs = {s: self.base_order[s]['inputs'] for s in self.sensors}
        self.input_names_all = set([s[0] for k, s in self.inputs.items()])

    def tearDown(self):
        # clean up orders
        self.mock_order.tear_down_testing_orders()
        # clean up users
        self.mock_user.cleanup()
        os.environ['espa_api_testing'] = ''

    def test_get_api_response_type(self):
        response = self.app.get('/api', headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(response.content_type, 'application/json')

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_api_response_content(self):
        response = self.app.get('/api', headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(set(['v1', 'v0']), set(resp_json.keys()))
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_api_info_response_content(self):
        response = self.app.get('/api/v1', headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn("Version 1", resp_json['description'])
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    @patch('api.providers.ordering.ordering_provider.OrderingProvider.available_products', mock_api.available_products)
    def test_get_available_prods(self):
        url = '/api/v1/available-products/' + ",".join(self.sceneids)
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn("etm", resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    @patch('api.providers.ordering.ordering_provider.OrderingProvider.available_products', mock_api.available_products)
    def test_get_available_prods_json(self):
        url = '/api/v1/available-products'
        data_dict = {'inputs': self.sceneids}
        response = self.app.get(url, data=json.dumps(data_dict), headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn('etm', resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_available_orders_user(self):
        url = "/api/v1/list-orders"
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIsInstance(resp_json, list)
        self.assertListEqual(resp_json, [self.orderid])
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_available_orders_email(self):
        # email param comes in as unicode
        url = "/api/v1/list-orders/" + str(self.user.email)
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIsInstance(resp_json, list)
        self.assertListEqual(resp_json, [self.orderid])
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_order_by_ordernum(self):
        url = "/api/v1/order/" + str(self.orderid)
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        items = {'orderid', 'note', 'order_source', 'order_type', 'product_opts',
                 'priority', 'completion_date', 'status', 'order_date', 'product_options'}
        self.assertEqual(items, set(resp_json))
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_order_status_by_ordernum(self):
        url = "/api/v1/order-status/" + str(self.orderid)
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual({'orderid', 'status'}, set(resp_json))
        self.assertEqual(self.orderid, resp_json.get('orderid'))
        self.assertEqual('ordered', resp_json.get('status'))
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_item_status_by_ordernum(self):
        url = "/api/v1/item-status/%s" % self.itemorderid
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        all_names = set([s['name'].lower() for s in resp_json[self.orderid]])
        all_names -= {'plot'}
        self.assertEqual(self.input_names_all, all_names)
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_item_status_by_ordernum_itemnum(self):
        url = "/api/v1/item-status/%s/%s" % (self.itemorderid, self.itemid)
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        all_names = set([s['name'].lower() for s in resp_json[self.orderid]])
        self.assertEqual({self.itemid.lower()}, all_names)
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_current_user(self):
        url = "/api/v1/user"
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn('username', resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_projections(self):
        url = '/api/v1/projections'
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn('aea', resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_formats(self):
        url = '/api/v1/formats'
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn('formats', resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_resampling(self):
        url = '/api/v1/resampling-methods'
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn('resampling_methods', resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_get_order_schema(self):
        url = '/api/v1/order-schema'
        response = self.app.get(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertIn('properties', resp_json.keys())
        self.assertEqual(200, response.status_code)

    @patch('api.domain.user.User.get', MockUser.get)
    def test_bad_method(self):
        url = '/api/v1/available-products/'
        response = self.app.post(url, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(405, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn('errors', resp_json['messages'])

    @patch('api.domain.user.User.get', MockUser.get)
    def test_bad_data(self):
        url = '/api/v1/order'
        data = '{"inputs": [}'
        response = self.app.post(url, data=data, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(400, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn('errors', resp_json['messages'])

    @patch('api.domain.user.User.get', MockUser.get)
    def test_bad_validation_inputs(self):
        url = '/api/v1/order'
        data = '{"inputs": []}'
        response = self.app.post(url, data=data, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(400, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn('errors', resp_json['messages'])
        self.assertIn('Schema errors',
                      resp_json['messages']['errors'][0])

    @patch('api.domain.user.User.get', MockUser.get)
    def test_bad_validation_sensor_inputs(self):
        url = '/api/v1/order'
        data = '{"etm7_collection": {"inputs": ["LE07_L1TP_010028_20050420_20160925_01_T1"]}}'
        response = self.app.post(url, data=data, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(400, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn('errors', resp_json['messages'])
        self.assertIn('2 validation errors', resp_json['messages']['errors'][0])

    @patch('api.domain.user.User.get', MockUser.get)
    def test_bad_data_avail_inputs(self):
        url = '/api/v1/available-products/'
        data = '{"bad": []}'
        response = self.app.get(url, data=data, headers=self.headers, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(400, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn('errors', resp_json['messages'])
        self.assertIn('No input products supplied', resp_json['messages']['errors'][0])

    @patch('api.external.ers.ERSApi._api_post', lambda x, y, z: {'errors': True})
    def test_messages_field_acc_denied(self):
        url = '/api/v1/available-products/'
        response = self.app.get(url, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(401, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn('errors', resp_json['messages'])

    @patch('api.domain.user.User.get', MockUser.get)
    def test_not_found(self):
        url = '/api/v1/not-valid'
        response = self.app.get(url, environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(404, response.status_code)
        self.assertIn('messages', resp_json)
        self.assertIn("errors", resp_json['messages'])

    @patch('api.domain.user.User.get', MockUser.get)
    @patch('api.interfaces.ordering.version1.API.place_order', MockOrder.place_order)
    def test_post_order(self):
        url = '/api/v1/order'
        data = {'etm7_collection': {'inputs': [''], 'products': ['']}}
        response = self.app.post(url, headers=self.headers, data=json.dumps(data), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(201, response.status_code)
        self.assertEqual({'orderid', 'status'}, set(resp_json.keys()))

    @patch('api.domain.user.User.get', MockUser.get)
    @patch('api.interfaces.ordering.version1.API.cancel_order', MockOrder.cancel_order)
    def test_cancel_order(self):
        url = '/api/v1/order'
        data = {'orderid': self.orderid, 'status': 'cancelled'}
        response = self.app.put(url, headers=self.headers, data=json.dumps(data), environ_base={'REMOTE_ADDR': '127.0.0.1'})
        resp_json = json.loads(response.get_data())
        self.assertEqual(data, resp_json)
        self.assertEqual(202, response.status_code)

if __name__ == '__main__':
    unittest.main()


