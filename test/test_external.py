import os
import unittest
from mock import patch, MagicMock

from api.external import onlinecache
from api.external.mocks import onlinecache as mockonlinecache
from api.external.mocks import inventory as mockinventory
from api.external import inventory


class TestLPDAAC(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


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
        self.assertIsInstance(token, str)
        self.assertTrue(inventory.logout(token))

    @patch('api.external.inventory.requests.head', mockinventory.RequestsSpoof)
    def test_api_available(self):
        self.assertTrue(inventory.available())

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_id_lookup(self):
        entity_ids = inventory.convert(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        self.assertEqual({'LC08_L1TP_156063_20170207_20170216_01_T1'}, set(entity_ids))

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_validation(self):
        results = inventory.verify_scenes(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        test = {'LC08_L1TP_156063_20170207_20170216_01_T1': True}
        self.assertDictEqual(test, results)

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_api_get_download_urls(self):
        entity_ids = inventory.convert(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        results = inventory.get_download_urls(self.token, ['LC08_L1TP_156063_20170207_20170216_01_T1'], 'LANDSAT_8_C1')
        self.assertIsInstance(results, dict)
        ehost, ihost = 'invalid.com', '127.0.0.1'
        results = {k: v.replace(ehost, ihost) for k,v in results.items()}
        self.assertEqual(set(entity_ids.values()), {'LC81560632017038LGN00'})
        ip_address_host_regex = r'http://\d+\.\d+\.\d+\.\d+/.*\.tar\.gz'
        for pid in entity_ids.values():
            self.assertRegexpMatches(results.get(pid), ip_address_host_regex)

    @patch('api.external.inventory.requests.get', mockinventory.RequestsSpoof)
    @patch('api.external.inventory.requests.post', mockinventory.RequestsSpoof)
    def test_clear_user_context(self):
        success = inventory.clear_user_context(self.token)
        self.assertTrue(success)


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
        self.assertIsInstance(token, str)


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


