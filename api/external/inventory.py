"""
TODO: Replaces lta.py
"""
import json
import urllib
import traceback
import datetime
import socket
import re
from itertools import groupby

import requests
import memcache

from api.domain import sensor
from api.providers.configuration.configuration_provider import (
    ConfigurationProvider)
from api.providers.caching.caching_provider import CachingProvider
from api.system.logger import ilogger as logger


config = ConfigurationProvider()



# -----------------------------------------------------------------------------+
# Find Documentation here:                                                     |
#      https://earthexplorer.usgs.gov/inventory/documentation/json-api         |
def split_by_dataset(product_ids):
    """
    Subset list of Collection IDs (LC08_...) by the LTA JSON data set name

    :param product_ids: Landsat Collection IDs ['LC08_..', ...]
    :type product_ids: list
    :return: dict
    """
    return {k: list(g) for k, g in groupby(sorted(product_ids),
                lambda x: sensor.instance(x).lta_json_name)}

class LTAError(Exception):
    pass

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

        self.external_landsat_regex = re.compile(config.url_for('landsat.external'))
        self.landsat_datapool = config.url_for('landsat.datapool')
        self.external_modis_regex = re.compile(config.url_for('modis.external'))
        self.modis_datapool = config.url_for('modis.datapool')

        if self.current_user and self.token:
            self.set_user_context(self.current_user, ipaddress=self.ipaddr)

    def network_urls(self, urls, sensor='landsat'):
        """ Convert External URLs to 'Internal' (on our 10GbE network) """
        match = {'landsat': self.landsat_datapool,
                 'modis': self.modis_datapool}[sensor]
        sub = {'landsat': self.external_landsat_regex.sub,
               'modis': self.external_modis_regex.sub}[sensor]
        return {k: sub(match, v) for k,v in urls.items()}

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
        data = None
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error('server reported bad status code: {}'
                           .format(e))
        try:
            data = response.json()
        except ValueError as e:
            msg = ('unable to parse JSON response. {}\n'
                   'traceback:\n{}'.format(e, traceback.format_exc()))
            logger.error(msg)

        if data.get('error'):
            logger.error('{errorCode}: {error}'.format(**data))
        if 'data' not in data:
            logger.error('no data found:\n{}'.format(data))

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
        url = self.base_url + 'login'
        logger.debug('HEAD {}'.format(url))
        resp = requests.head(url)
        return resp.ok

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
            logger.error('{} logout failed'.format(self.current_user))

    def easy_id_lookup(self, product_ids):
        retdata = dict()
        for sensor_name, id_list in split_by_dataset(product_ids).items():
             retdata.update(self.id_lookup(id_list, sensor_name))
        return retdata

    def id_lookup(self, product_ids, dataset):
        """
        Convert Collection IDs (LC08_...) into M2M entity IDs

        :param product_ids: Landsat Collection IDs ['LC08_..', ...]
        :type product_ids: list
        :return: dict
        """
        endpoint = 'idLookup'
        id_list = [i for i in product_ids]
        if dataset.startswith('MODIS'):
            # WARNING: MODIS dataset does not have processed date
            #           in M2M entity lookup!
            id_list = [i.rsplit('.',1)[0] for i in id_list]
        payload = dict(apiKey=self.token,
                        idList=id_list,
                        inputField='displayId', datasetName=dataset)
        resp = self._post(endpoint, payload)
        results = resp.get('data')

        id_list = [i for i in product_ids]
        if dataset.startswith('MODIS'):
            # WARNING: See above. Need to "undo" the MODIS mapping problem.
            results = {[i for i in id_list if k in i
                        ].pop(): v for k,v in results.items()}
        return {k: results.get(k) for k in id_list}

    def verify_scenes(self, product_ids, dataset):
        """
        Check if supplied IDs successfully mapped to M2M entity IDs

        :param product_ids: Landsat Collection IDs ['LC08_..', ...]
        :type product_ids: list
        :return: dict
        """
        entity_ids = self.id_lookup(product_ids, dataset)
        return {k: entity_ids.get(k) is not None for k in product_ids}

    def get_download_urls(self, entity_ids, dataset, products='STANDARD',
                          stage=True, usage='[espa]:sr'):
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
        payload = dict(apiKey=self.token, datasetName=dataset,
                        products=products, entityIds=entity_ids,
                        stage=stage, dataUse=usage)
        resp = self._post('download', payload)
        results = resp.get('data')
        return self.network_urls(
                   self.network_urls(
                       {i['entityId']: i['url'] for i in results},
                    'landsat'), 'modis')

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
        self.cache = CachingProvider(timeout=one_hour)

    def get_login(self):
        cache_key = self.MC_KEY_FMT.format(resource='login')
        token = self.cache.get(cache_key)
        return token

    def set_login(self, token):
        cache_key = self.MC_KEY_FMT.format(resource='login')
        success = self.cache.set(cache_key, token)
        if not success:
            logger.error('LTACachedService: Token not cached')

    def cached_login(self):
        token = self.get_login()
        if token is None:
            token = self.login()
            self.set_login(token)
        return token


''' This is the public interface that calling code should use to interact
    with this module'''


def get_session():
    return LTAService().login()


def logout(token):
    return LTAService(token).logout()


def convert(token, product_ids, dataset):
    return LTAService(token).id_lookup(product_ids, dataset)


def verify_scenes(token, product_ids, dataset):
    return LTAService(token).verify_scenes(product_ids, dataset)


def get_download_urls(token, entity_ids, dataset, usage='[espa]'):
    return LTAService(token).get_download_urls(entity_ids, dataset, usage=usage)


def set_user_context(token, contactid, ipaddress=None):
    return LTAService(token).set_user_context(contactid, ipaddress)


def clear_user_context(token):
    return LTAService(token).clear_user_context()


def available():
    return LTAService().available()


def check_valid(token, product_ids):
    return dict(z for d, l in split_by_dataset(product_ids).items()
                 for z in verify_scenes(token, l, d).items())


def download_urls(token, product_ids, dataset, usage='[espa]'):
    entities = convert(token, product_ids, dataset)
    urls = get_download_urls(token, entities.values(), dataset, usage=usage)
    return {p: urls.get(e) for p, e in entities.items() if e in urls}


def get_cached_session():
    return LTACachedService().cached_login()
