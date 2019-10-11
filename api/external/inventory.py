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
from api.providers.configuration.configuration_provider import ConfigurationProvider
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

        return {k: sub(match, v) for k, v in urls.items()}

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

        # We need to include the .h5 file extension when verifying viirs scene IDs
        if dataset.startswith('VIIRS'):
            viirs_ext = '.h5'
            id_list = [i + viirs_ext for i in id_list if not i.endswith(viirs_ext)]

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

        if dataset.startswith('VIIRS'):
            # Undo the file extension addition from above
            results = {[i for i in id_list if i in k].pop(): v for k, v in results.items()}
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

        if results:
            # Use the URL taken directly from the M2M JSON API if VIIRS
            if 'VNP' in dataset:
                return {i['entityId']: i['url'] for i in results}
            # For now, let's keep the original M2M download url for sentinel
            elif 'SENTINEL' in dataset:
                return {i['entityId']: i['url'] for i in results}
            # Otherwise use our internal network conversion
            else:
                return self.network_urls(
                    self.network_urls({i['entityId']: i['url'] for i in results},
                                      'landsat'), 'modis')
        else:
            logger.warn("inventory.get_download_urls - no data in POST response returned for entity_ids: {}, dataset: {}".format(entity_ids, dataset))
            

    def get_order_status(self, order_number):
        """
        Return the order status for the given order number.
        
        :param order_number: EE order id
        :type order_number: string
        """
        endpoint  = 'orderstatus'
        payload   = dict(apiKey=self.token, orderNumber=order_number)
        response  = self._post(endpoint, payload)
        result    = response.get('data')
        errorCode = response.get('errorCode')
        error     = response.get('error')
        # result keys: 'orderNumber', 'units', 'statusCode', 'statusText'
        # 'units' dicts keys: 'datasetName', 'displayId', 'entityId', 'orderingid',
        #                     'productCode', 'productDescription', 'statusCode',
        #                     'statusText', 'unitNumber'
        return result
        
    def update_order_status(self, order_number, unit_number, status):
        """
        Update the status of orders ESPA is working on.

        :param order_number: EE order id
        :type  order_number: string
        :param unit_number:  id for unit to update
        :type  unit_number:  string
        :param status:       the EE defined status value
        :type  status:       string
        """
        endpoint = 'setunitstatus'
        payload  = dict(apiKey=self.token, orderNumber=order_number, unitStatus=status, 
                        firstUnitNumber=unit_number, lastUnitNumber=unit_number)
        response = self._post(endpoint, payload)
        error    = response.get('error')

        # according to v1.4.1 api docs, 
        # "This request does not have a response. Successful execution is assumed if no errors are thrown."
        if not error:
            return {'success': True, 'message': None, 'status': None}
        else:
            # throw exception if non 200 response?
            logger.error("Problem updating order status in EE. order_number: {}  unit_number: {}  status: {}  response: {}".format(order_number, unit_number, status, response))
            return {'success': False, 'message': response, 'status': 'Fail'}

    def get_available_orders(self, contactid=None):
        """
        Return collection of ESPA orders from EE
        """
        endpoint = 'getorderqueue'
        payload = dict(apiKey=self.token, queueName='espa')
        response = self._post(endpoint, payload)
        data = response.get('data')
        orders = []


        if isinstance(data, dict) and 'orders' in data.keys():
            if contactid:
              orders = [o for o in data.get('orders') if o.get('contactId') == contactid] 
            else:
              orders = data.get('orders')
        else:
            logger.error("Problem retrieving available orders from M2M. response: {}".format(response))

        return orders

## sample response, now includes contactId
# {u'access_level': u'appuser',
#  u'api_version': u'1.4.1',
#  u'catalog_id': u'EE',
#  u'data': {u'orders': [{u'contactId': 888718,
#                         u'orderNumber': u'0101905173361',
#                         u'statusCode': u'Q',
#                         u'statusText': u'Queued for Processing',
#                         u'units': [{u'datasetName': None,
#                                     u'displayId': None,
#                                     u'entityId': None,
#                                     u'orderingId': u'LT05_L1GS_125061_19871229_20170210_01_T2',
#                                     u'productCode': u'SR05',
#                                     u'productDescription': u'LANDSAT TM COLLECTIONS LAND SURFACE REFLECTANCE ON-DEMAND',
#                                     u'statusCode': None,
#                                     u'statusText': None,
#                                     u'unitNumber': 1}]},

    def get_user_email(self, contactid):
        """
        This method will get the end-user lookup data given a contactid.

        :param contactid: ERS identification key (number form
        :type contactid: int
        :return: dictionary
        """
        endpoint = 'userLookup'
        payload = dict(apiKey=self.token, contactId=int(contactid))
        resp = self._post(endpoint, payload)
        if not bool(resp.get('data')):
            raise LTAError('Get user email failed for contactid {}'.format(contactid))
        return str(resp.get('data'))

    def get_user_context(self, contactid, ipaddress=None, context='ESPA'):
        """
        This method will get the end-user details given a contactid.

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
            raise LTAError('Get user context {} failed for user {} (ip: {})'
                           .format(context, contactid, ipaddress))
        return resp.get('data')

    def set_user_context(self, contactid, ipaddress=None, context='ESPA'):
        """
        This method will set the end-user context for all subsequent requests.

        :param contactid: ERS identification key (number form
        :type contactid: int
        :param ipaddress: Originating IP Address
        :param context: Usage statistics that are executed via 'M2M_APP' users
        :return: bool
        """
        if self.get_user_context(contactid, ipaddress, context):
            self.current_user = contactid
            return True
        else:
            return False

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


# unused, remove?
#def get_user_context(token, contactid, ipaddress=None):
#    return LTAService(token).get_user_context(contactid, ipaddress)

# unused, remove?
#def set_user_context(token, contactid, ipaddress=None):
#    return LTAService(token).set_user_context(contactid, ipaddress)


def get_user_name(token, contactid, ipaddress=None):
    context = LTAService(token).get_user_context(contactid, ipaddress)
    return str(context.get('username'))

def get_user_details(token, contactid, ipaddress=None):
    email    = LTAService(token).get_user_email(contactid)
    username = get_user_name(token, contactid, ipaddress)
    return username, email

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

def get_order_status(token, order_number):
    return LTAService(token).get_order_status(order_number)

def update_order_status(token, order_number, unit_number, status):
    return LTAService(token).update_order_status(order_number, unit_number, status)

def get_available_orders(token, contactid=None):
    return LTAService(token).get_available_orders(contactid)
