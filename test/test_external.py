import os
import unittest
from mock import patch, MagicMock

from test.version0_testorders import build_base_order
from api.external import onlinecache
from api.external.mocks import onlinecache as mockonlinecache
from api.external.mocks import hadoop as mockhadoop
from api.external import lta
from api.external.mocks import lta as mocklta
from api.external.hadoop import HadoopHandler
from api.external.mocks import inventory as mockinventory

from api.external import lpdaac
from api.external import inventory
from api import ProductNotImplemented

class TestLPDAAC(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass



class TestLTA(unittest.TestCase):
    def setUp(self):
        os.environ['espa_api_testing'] = 'True'
        self.contact_id = 0
        self.lta_order_number = 0
        self.lta_unit_number = 0
        base_order = build_base_order()
        self.scene_ids = [base_order[b].get('inputs', [None]).pop() for b in base_order if type(base_order[b]) == dict]
        self.scene_ids = [s for s in self.scene_ids if s and (s.startswith('L'))]  # Landsat only

    def tearDown(self):
        os.environ['espa_api_testing'] = ''

    #@patch('api.external.lta.OrderUpdateServiceClient.update_order', mocklta.return_update_order_resp)
    @patch('api.external.lta.SoapClient', mocklta.MockSudsClient)
    def test_get_available_orders(self):
        resp = lta.get_available_orders()
        self.assertEqual(len(resp[('100', '', '')]), 3)

    @patch('api.external.lta.SoapClient', mocklta.MockSudsClient)
    def test_get_order_status(self):
        resp = lta.get_order_status(self.lta_order_number)
        self.assertIn('order_status', resp)
        self.assertEqual(resp['order_num'], str(self.lta_order_number))

    @patch('api.external.lta.SoapClient', mocklta.MockSudsClient)
    def test_update_order_complete(self):
        resp = lta.update_order_status(self.lta_order_number, self.lta_unit_number, 'C')
        self.assertTrue(resp.success)

    @patch('api.external.lta.SoapClient', mocklta.MockSudsClient)
    def test_update_order_incomplete(self):
        resp = lta.update_order_status('failure', self.lta_unit_number, 'C')
        self.assertFalse(resp.success)


class TestInventory(unittest.TestCase):
    """
    Provide testing for the EarthExplorer JSON API (Machine-2-Machine)
    """
    def setUp(self):
        os.environ['espa_api_testing'] = 'True'
        self.token = '2fd976601eef1ebd632b545a8fef11a3'
        self.usage = 'espa-production@email.com-20170801-01-01'
        self.collection_ids = ['LC08_L1TP_156063_20170207_20170216_01_T1',
                               'LE07_L1TP_028028_20130510_20160908_01_T1',
                               'LT05_L1TP_032028_20120425_20160830_01_T1']
        self.contact_id = 0

    def tearDown(self):
        os.environ['espa_api_testing'] = ''

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_login(self):
        token = inventory.get_session()
        self.assertIsInstance(token, basestring)
        self.assertTrue(inventory.logout(token))

    @patch('api.external.inventory.requests.head', mockinventory.RequestsSpoof)
    def test_api_available(self):
        self.assertTrue(inventory.available())

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_id_lookup(self):
        entity_ids = inventory.convert(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        self.assertEqual(set(['LC08_L1TP_156063_20170207_20170216_01_T1']), set(entity_ids))

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_validation(self):
        expected = {k: True for k in self.collection_ids}
        results = inventory.verify_scenes(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        self.assertItemsEqual({'LC08_L1TP_156063_20170207_20170216_01_T1': True}, results)

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_get_download_urls(self):
        entity_ids = inventory.convert(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        results = inventory.get_download_urls(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        self.assertIsInstance(results, dict)
        ehost, ihost = 'invalid.com', '127.0.0.1'
        results = {k:v.replace(ehost, ihost) for k,v in results.items()}
        self.assertEqual(set(entity_ids.values()), set(['LC81560632017038LGN00']))
        ip_address_host_regex = 'http://\d+\.\d+\.\d+\.\d+/.*\.tar\.gz'
        for pid in entity_ids.values():
            self.assertRegexpMatches(results.get(pid), ip_address_host_regex)

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_set_user_context(self):
        success = inventory.set_user_context(self.token, self.contact_id)
        self.assertTrue(success)

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_clear_user_context(self):
        success = inventory.clear_user_context(self.token)
        self.assertTrue(success)

#    def test_id_sensor_limits(self):
#        with self.assertRaisesRegexp(ProductNotImplemented, 'is not a supported sensor product'):
#            _ = inventory.convert(self.token, self.contact_id, ['bad_id_yo'])
#
#    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
#    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
#    def test_bad_id_lookup(self):
#        with self.assertRaisesRegexp(inventory.LTAError, 'ID Lookup failed'):
#            _ = inventory.convert(self.token, self.contact_id, ['LC08_L1TP_000000_19000101_00000000_00_T1'])
#
#    @patch('api.external.inventory.requests.post', mockinventory.BadRequestSpoofError)
#    def test_error_code_halt(self):
#        expected = 'UNKNOWN: A fake server error occurred'
#        with self.assertRaisesRegexp(inventory.LTAError, expected):
#            _ = inventory.get_session()
#
#    @patch('api.external.inventory.requests.get', mockinventory.BadRequestSpoofNegative)
#    @patch('api.external.inventory.requests.post', mockinventory.BadRequestSpoofNegative)
#    def test_false_data_response(self):
#        expected = 'Set user context ESPA failed for user {}'.format(self.contact_id)
#        with self.assertRaisesRegexp(inventory.LTAError, expected):
#            _ = inventory.set_user_context(self.token, self.contact_id)
#

class TestCachedInventory(unittest.TestCase):
    """
    Provide testing for the CACHED EarthExplorer JSON API
        (FIXME: this still requires an active memcached session)
    """
    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def setUp(self):
        os.environ['espa_api_testing'] = 'True'
        self.token = inventory.get_cached_session()  # Initial "real" request
        self.collection_ids = ['LC08_L1TP_156063_20170207_20170216_01_T1',
                               'LE07_L1TP_028028_20130510_20160908_01_T1',
                               'LT05_L1TP_032028_20120425_20160830_01_T1']
        #_ = inventory.get_cached_convert(self.token, self.collection_ids)
        #_ = inventory.get_cached_verify_scenes(self.token, self.collection_ids)

    def tearDown(self):
        os.environ['espa_api_testing'] = ''

    @patch('api.external.inventory.requests.post', mockinventory.CachedRequestPreventionSpoof)
    def test_cached_login(self):
        token = inventory.get_cached_session()
        self.assertIsInstance(token, basestring)

    #@patch('api.external.inventory.requests.get', mockinventory.CachedRequestPreventionSpoof)
    #@patch('api.external.inventory.requests.post', mockinventory.CachedRequestPreventionSpoof)
    #def test_cached_lookup(self):
    #    entity_ids = inventory.get_cached_convert(self.token, self.collection_ids)
    #    self.assertEqual(set(self.collection_ids), set(entity_ids))

    #@patch('api.external.inventory.requests.get', mockinventory.CachedRequestPreventionSpoof)
    #@patch('api.external.inventory.requests.post', mockinventory.CachedRequestPreventionSpoof)
    #def test_cached_verify_scenes(self):
    #    expected = {k: True for k in self.collection_ids}
    #    results = inventory.get_cached_verify_scenes(self.token, self.collection_ids)
    #    self.assertItemsEqual(expected, results)


class TestOnlineCache(unittest.TestCase):
    """
    Tests for dealing with the distribution cache
    """
    @patch('api.external.onlinecache.OnlineCache.execute_command', mockonlinecache.list)
    @patch('api.external.onlinecache.sshcmd')
    def setUp(self, MockSSHCmd):
        os.environ['espa_api_testing'] = 'True'
        MockSSHCmd.return_value = MagicMock()
        self.cache = onlinecache.OnlineCache()

    def tearDown(self):
        os.environ['espa_api_testing'] = ''

    @patch('api.external.onlinecache.OnlineCache.execute_command', mockonlinecache.list)
    def test_cache_listorders(self):
        results = self.cache.list()

        self.assertTrue(results)

    @patch('api.external.onlinecache.OnlineCache.execute_command', mockonlinecache.capacity)
    def test_cache_capcity(self):
        results = self.cache.capacity()

        self.assertTrue('capacity' in results)

    @patch('api.external.onlinecache.OnlineCache.exists', lambda x, y, z: True)
    @patch('api.external.onlinecache.OnlineCache.execute_command', mockonlinecache.delete)
    def test_cache_deleteorder(self):
        results = self.cache.delete('bilbo')
        self.assertTrue(results)


class TestHadoopHandler(unittest.TestCase):
    """
    Tests for the hadoop interaction class
    """
    def setUp(self):
        os.environ['espa_api_testing'] = 'True'
        self.hadoop = HadoopHandler()

    def tearDown(self):
        os.environ['espa_api_testing'] = ''

    @patch('api.external.hadoop.HadoopHandler._remote_cmd', mockhadoop.list_jobs)
    def test_list_jobs(self):
        resp = self.hadoop.list_jobs()
        self.assertIsInstance(resp, dict)
        for key, value in resp.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)

    @patch('api.external.hadoop.HadoopHandler.job_names_ids', mockhadoop.jobs_names_ids)
    def test_job_names_ids(self):
        resp = self.hadoop.job_names_ids()
        self.assertIsInstance(resp, dict)

    @patch('api.external.hadoop.HadoopHandler._remote_cmd', mockhadoop.slave_ips)
    def test_slave_ips(self):
        resp = self.hadoop.slave_ips()
        self.assertIsInstance(resp, list)
        self.assertTrue(len(resp) > 0)

    @patch('api.external.hadoop.HadoopHandler.master_ip', mockhadoop.master_ip)
    def test_master_ip(self):
        resp = self.hadoop.master_ip()
        self.assertIsInstance(resp, str)
        self.assertTrue(len(resp.split('.')) == 4)

