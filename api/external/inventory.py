"""
TODO: Replaces lta.py
"""
import json
import urllib
import traceback
import datetime
import socket

import requests
import memcache

from api.domain import sensor
from api.providers.configuration.configuration_provider import (
    ConfigurationProvider)
from api.providers.caching.caching_provider import CachingProvider
from api.system.logger import ilogger as logger


config = ConfigurationProvider()


class LTAError(Exception):
    def __init__(self, message):
        logger.error('ERR %s', message)
        super(LTAError, self).__init__(message)


# -----------------------------------------------------------------------------+
# Find Documentation here:                                                     |
#      https://earthexplorer.usgs.gov/inventory/documentation/json-api         |
class LTAService(object):
    def __init__(self, token=None, current_user=None, ipaddr=None):
        mode = config.mode
        self.api_version = config.get('bulk.{0}.json.version'.format(mode))
        self.agent = config.get('bulk.{0}.json.username'.format(mode))
        self.agent_wurd = config.get('bulk.{0}.json.password'.format(mode))
        self.base_url = config.url_for('earthexplorer.json')
        self.current_user = current_user  # CONTACT ID
        self.token = token
        self.ipaddr = ipaddr or socket.gethostbyaddr(socket.gethostname())[2][0]

        self.external_landsat_hosts = config.url_for('landsat.external').split(',')
        self.landsat_datapool = config.url_for('landsat.datapool')
        self.external_modis_hosts = config.url_for('modis.external').split(',')
        self.modis_datapool = config.url_for('modis.datapool')

        if self.current_user and self.token:
            self.set_user_context(self.current_user, ipaddress=self.ipaddr)

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        if not isinstance(value, basestring):
            raise TypeError('LTAService base_url must be string')
        self._base_url = value

    @staticmethod
    def _parse(response):
        """
        Attempt to parse the JSON response, which always contains additional
        information that we might not always want to look at (except on error)

        :param response: requests.models.Response
        :return: dict
        """
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise LTAError('server reported bad status code: {}'
                           .format(e))
        try:
            data = response.json()
        except ValueError as e:
            msg = ('unable to parse JSON response. {}\n'
                   'traceback:\n{}'.format(e, traceback.format_exc()))
            raise LTAError(msg)

        if data.get('error'):
            raise LTAError('{errorCode}: {error}'.format(**data))
        if 'data' not in data:
            raise LTAError('no data found:\n{}'.format(data))

        return data

    def _request(self, endpoint, data=None, verb='post'):
        """
        Wrapper function for debugging connectivity issues

        :param endpoint: the resource location on the host
        :param data: optional message body
        :param verb: HTTP method of GET or POST
        :return:
        """
        url = self.base_url + endpoint
        if data:
            data = {'jsonRequest': json.dumps(data)}
        logger.debug('[%s] %s', verb.upper(), url)
        if 'password' not in str(data):
            logger.debug('Payload: {}'.format(data))
        # Note: using `data=` (to force form-encoded params)
        response = getattr(requests, verb)(url, data=data)
        logger.debug('[RESPONSE] %s\n%s', response, response.content)
        return self._parse(response)

    def _get(self, endpoint, data=None):
        return self._request(endpoint, data, verb='get')

    def _post(self, endpoint, data=None):
        return self._request(endpoint, data, verb='post')

    # Formatting wrappers on resource endpoints ================================
    def login(self):
        """
        Authenticates the user-agent and returns an API Key

        :return: str
        """
        endpoint = 'login'
        payload = dict(username=self.agent, password=self.agent_wurd,
                       authType='EROS', catalogId='EE')
        resp = self._post(endpoint, payload)
        return resp.get('data')

    def available(self):
        """
        Checks the LTA API status endpoint

        :return: bool
        """
        endpoint = 'login'
        payload = dict(username=self.agent, password=self.agent_wurd,
                       authType='EROS')
        resp = self._post(endpoint, payload)
        return resp.get('data') is not None

    def logout(self):
        """
        Remove the users API key from being used in the future

        :return: bool
        """
        endpoint = 'logout'
        payload = dict(apiKey=self.token)
        resp = self._post(endpoint, payload)
        if resp.get('data'):
            return True
        else:
            raise LTAError('{} logout failed'.format(self.current_user))

    @staticmethod
    def split_by_dataset(product_ids):
        """
        Subset list of Collection IDs (LC08_...) by the LTA JSON data set name

        :param product_ids: Landsat Collection IDs ['LC08_..', ...]
        :type product_ids: list
        :return: dict
        """
        retdata = dict()
        instances = [sensor.instance(p) for p in product_ids]
        sensors = set([s.lta_json_name for s in instances])
        for s_name in sensors:
            retdata[s_name] = [s.product_id for s in instances
                               if s.lta_json_name == s_name]
        return retdata

    def id_lookup(self, product_ids):
        """
        Convert Collection IDs (LC08_...) into M2M entity IDs

        :param product_ids: Landsat Collection IDs ['LC08_..', ...]
        :type product_ids: list
        :return: dict
        """
        dataset_groups = self.split_by_dataset(product_ids)
        endpoint = 'idLookup'
        retdata = dict()
        for sensor_name in dataset_groups:
            id_list = dataset_groups[sensor_name]
            payload = dict(apiKey=self.token,
                           idList=id_list,
                           inputField='displayId', datasetName=sensor_name)
            resp = self._post(endpoint, payload)
            results = resp.get('data')
            if not isinstance(results, dict):
                raise LTAError('{} ID Lookup failed: {}'
                               .format(sensor_name, product_ids))
            diff = set(id_list) - set(results.keys())
            if diff:
                raise LTAError('ID Lookup failed for: {}'.format(diff))
            else:
                entity_ids = {k: results.get(k) for k in id_list}
                retdata.update(entity_ids)
        return retdata

    def verify_scenes(self, product_ids):
        """
        Check if supplied IDs successfully mapped to M2M entity IDs

        :param product_ids: Landsat Collection IDs ['LC08_..', ...]
        :type product_ids: list
        :return: dict
        """
        entity_ids = self.id_lookup(product_ids)
        diff = set(product_ids) - set(entity_ids)
        if diff:
            raise LTAError('Verify scenes failed for: {}'.format(diff))

        results = {k: k in entity_ids.keys() for k in product_ids}
        return results

    def get_download_urls(self, product_ids, products='STANDARD', stage=True,
                          usage='[espa]:sr'):
        """
        Fetch the download location for supplied IDs, replacing the public host
            with an internal network host (to bypass public firewall routing)

        :param product_ids: Landsat Collection IDs ['LC08_..', ...]
        :type product_ids: list
        :param products: download type to grab (STANDARD is for L1-GeoTIFF)
        :type products: str
        :param stage: If true, initiates a data stage command
        :type stage: bool
        :param usage: Identify higher level products this data is used to create
        :type usage: str
        :return: dict
        """
        dataset_groups = self.split_by_dataset(product_ids)
        entity_ids = self.id_lookup(product_ids)
        endpoint = 'download'

        retdata = dict()
        for sensor_name in dataset_groups:
            id_list = dataset_groups[sensor_name]
            ents = [entity_ids.get(i) for i in id_list]
            payload = dict(apiKey=self.token, datasetName=sensor_name,
                           products=products, entityIds=ents, stage=stage,
                           dataUse=usage)
            resp = self._post(endpoint, payload)
            results = resp.get('data')
            if not isinstance(results, list):
                raise LTAError('{} failed fetch download urls: {}'
                               .format(sensor_name, product_ids))
            urls = {i['entityId']: i['url'] for i in results}
            for host in self.external_landsat_hosts:
                urls = {k:v.replace(host, self.landsat_datapool)
                        for k,v in urls.items()}
            for host in self.external_modis_hosts:
                urls = {k:v.replace(host, self.modis_datapool)
                        for k,v in urls.items()}

            diff = set(ents) - set(urls)
            if diff:
                raise LTAError('No download urls found for: {}'.format(diff))
            else:
                retdata.update(urls)
        return retdata

    def set_user_context(self, contactid, ipaddress=None, context='ESPA'):
        """
        This method will set the end-user context for all subsequent requests.

        :param contactid: ERS identification key (number form
        :type contactid: int
        :param ipaddress: Originating IP Address
        :param context: Usage statistics that are executed via 'M2M_APP' users
        :return: bool
        """
        endpoint = 'userContext'
        payload = dict(apiKey=self.token, contactId=int(contactid),
                       ipAddress=ipaddress, applicationContext=context)
        resp = self._post(endpoint, payload)
        if not bool(resp.get('data')):
            raise LTAError('Set user context {} failed for user {} (ip: {})'
                           .format(context, contactid, ipaddress))
        self.current_user = contactid
        return True

    def clear_user_context(self):
        """
        Clear out current session user context (reverts to auth'd user)

        :return: bool
        """
        endpoint = 'clearUserContext'
        payload = dict(apiKey=self.token)
        resp = self._post(endpoint, payload)
        if not bool(resp.get('data')):
            raise LTAError('Failed unset user context')
        self.current_user = None
        return True


class LTACachedService(LTAService):
    """
    Wrapper on top of the cache, with helper functions which balance requests
     to the external service when needed.
    """
    def __init__(self, *args, **kwargs):
        super(LTACachedService, self).__init__(*args, **kwargs)
        # TODO: need to profile how much data we are caching
        one_hour = 3600  # seconds
        self.MC_KEY_FMT = '({resource})'
        self.MD_KEY_FMT = '({resource},{id})'
        self.cache = CachingProvider(timeout=one_hour)

    # -----------------------------------------------------------------------+
    # Handlers to format cache keys and perform bulk value fetching/setting  |
    def get_login(self):
        cache_key = self.MC_KEY_FMT.format(resource='login')
        token = self.cache.get(cache_key)
        return token

    def set_login(self, token):
        cache_key = self.MC_KEY_FMT.format(resource='login')
        success = self.cache.set(cache_key, token)
        if not success:
            raise LTAError('Token not cached')

    def get_lookup(self, id_list):
        cache_keys = [self.MD_KEY_FMT.format(resource='idLookup', id=i)
                      for i in id_list]
        entries = self.cache.get_multi(cache_keys)
        entries = {k.split(',')[1][:-1]: v for k, v in entries.items()}
        return entries

    def set_lookup(self, id_pairs):
        cache_entries = {self.MD_KEY_FMT.format(resource='idLookup', id=i): e
                         for i, e in id_pairs.items()}
        success = self.cache.set_multi(cache_entries)
        if not success:
            raise LTAError('ID conversion not cached')

    # ---------------------------------------------------------------+
    # Handlers to balance fetching cached/external values as needed  |
    def cached_login(self):
        token = self.get_login()
        if token is None:
            token = self.login()
            self.set_login(token)
        return token

    def cached_id_lookup(self, id_list):
        entities = self.get_lookup(id_list)
        if len(entities) > 0:
            diff = set(id_list) - set(entities)
            if diff:
                fetched = self.id_lookup(list(diff))
                self.set_lookup(entities)
                entities.update(fetched)
        else:
            entities = self.id_lookup(id_list)
            self.set_lookup(entities)
        return entities

    def cached_verify_scenes(self, id_list):
        entities = self.get_lookup(id_list)
        if len(entities) > 0:
            diff = set(id_list) - set(entities)
            if diff:
                fetched = self.id_lookup(list(diff))
                self.set_lookup(entities)
                entities.update(fetched)
        else:
            entities = self.id_lookup(id_list)
            self.set_lookup(entities)
        results = {k: entities.get(k) for k in id_list}
        return results


''' This is the public interface that calling code should use to interact
    with this module'''


def get_session():
    return LTAService().login()


def available(token):
    return LTAService(token).available()


def logout(token):
    return LTAService(token).logout()


def convert(token, contactid, product_ids):
    return LTAService(token, contactid).id_lookup(product_ids)


def verify_scenes(token, contactid, product_ids):
    return LTAService(token, contactid).verify_scenes(product_ids)


def get_download_urls(token, contactid, product_ids, usage):
    return LTAService(token, contactid).get_download_urls(product_ids, usage=usage)


def set_user_context(token, contactid, ipaddress=None):
    return LTAService(token).set_user_context(contactid, ipaddress)


def clear_user_context(token):
    return LTAService(token).clear_user_context()


def get_cached_session():
    return LTACachedService().cached_login()


def get_cached_convert(token, product_ids):
    return LTACachedService(token).cached_id_lookup(product_ids)


def get_cached_verify_scenes(token, product_ids):
    return LTACachedService(token).cached_verify_scenes(product_ids)

