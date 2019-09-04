import copy
from api.domain.scene import Scene

RESOURCE_DEF = {
    'login': {
        "errorCode": None,
        "error": "",
        "data": "2fd976601eef1ebd632b545a8fef11a3",
        "api_version": "1.4.1"
    },
    'logout': {
        "errorCode": None,
        "error": "",
        "data": True,
        "api_version": "1.4.1"
    },
    'idLookup': {
        "errorCode": None,
        "error": "",
        "data": {
            "LC08_L1TP_156063_20170207_20170216_01_T1": "LC81560632017038LGN00",
            "LE07_L1TP_028028_20130510_20160908_01_T1": "LE70280282013130EDC00",
            "LT05_L1TP_032028_20120425_20160830_01_T1": "LT50320282012116EDC00",
            "INVALID_ID": None
        }
    },
    'download': {
        "errorCode": None,
        "error": "",
        "data": [
            {"entityId": "LC81560632017038LGN00",
             "product": "STANDARD",
             "url": "http://invalid.com/path/to/downloads/l1/2014/013/029/LC81560632017038LGN00.tar.gz?iid=LC81560632017038LGN00&amp;did=63173803&amp;ver="},
            {"entityId": "LE70280282013130EDC00",
             "product": "STANDARD",
             "url": "http://invalid.com/path/to/downloads/l1/2014/013/029/LE70280282013130EDC00.tar.gz?iid=LE70280282013130EDC00&amp;did=63173803&amp;ver="},
            {"entityId": "LT50320282012116EDC00",
             "product": "STANDARD",
             "url": "http://invalid.com/path/to/downloads/l1/2014/013/029/LT50320282012116EDC00.tar.gz?iid=LT50320282012116EDC00&amp;did=63173803&amp;ver="}
        ],
        "api_version": "1.4.1"
    },
    'userContext': {
        "errorCode": None,
        "error": "",
        "data": True
    },
    'clearUserContext': {
        "errorCode": None,
        "error": "",
        "data": True
    }
}


class RequestsSpoof(object):
    def __init__(self, *args, **kwargs):
        self.url = args[0]
        self.resource = self.url.split('/')[-1]

        self.ok = True
        self.data = RESOURCE_DEF.get(self.resource)
        self.content = str(self.data)

    def __repr__(self):
        message = ('REQUEST SPOOF'
                   '\n\tURL: {}'
                   '\n\tRESOURCE: {}'
                   '\n\tDATA:{}').format(self.url, self.resource, self.data)
        return message

    def json(self):
        return self.data

    def raise_for_status(self):
        pass


class BadRequestSpoofError(RequestsSpoof):
    def __init__(self, *args, **kwargs):
        super(BadRequestSpoofError, self).__init__(*args, **kwargs)
        self.data = copy.deepcopy(self.data)

        if 'data' in self.data:
            self.data['data'] = None
        if 'errorCode' in self.data:
            self.data['errorCode'] = 'UNKNOWN'
        if 'error' in self.data:
            self.data['error'] = 'A fake server error occurred'


class BadRequestSpoofNegative(RequestsSpoof):
    def __init__(self, *args, **kwargs):
        super(BadRequestSpoofNegative, self).__init__(*args, **kwargs)
        self.data = copy.deepcopy(self.data)

        if 'data' in self.data and isinstance(self.data.get('data'), bool):
            self.data['data'] = not(self.data.get('data'))


class CachedRequestPreventionSpoof(object):
    def __init__(self, *args, **kwargs):
        raise RuntimeError('Should only require Cached values!')


# ----------------------------------------+
# Validation API testing                  |
def get_cache_values(self, product_list):
    response = {i: 'LC08_L1TP_025027_20160521_20170223_01_T1' for i in product_list}
    return response


# ----------------------------------------+
# Production API testing                  |
def get_download_urls(token, contactid, product_list, usage):
    response = {'LC08_L1TP_025027_20160521_20170223_01_T1': 'http://one_time_use.tar.gz' for i in product_list}
    return response

def get_cached_convert(token, product_list):
    response = {i: 'LC08_L1TP_025027_20160521_20170223_01_T1' for i in product_list}
    return response

def get_cached_session():
    return '2fd976601eef1ebd632b545a8fef11a3'

def check_valid_landsat(token, prod_name_list):
    _scenes = Scene.where({"status":"submitted", "sensor_type":"landsat"})
    _names = [s.name for s in _scenes]
    return {_names[0]: True}

def check_valid_modis(token, prod_name_list):
    _scenes = Scene.where({"status":"submitted", "sensor_type":"modis"})
    _names = [s.name for s in _scenes]
    return {_names[0]: True}

def check_valid_modis_unavailable(token, prod_name_list):
    _scenes = Scene.where({"status":"submitted", "sensor_type":"modis"})
    _names = [s.name for s in _scenes]
    return {_names[0]: False}


def check_valid_viirs(token, prod_name_list):
    _scenes = Scene.where({"status":"submitted", "sensor_type":"viirs"})
    _names = [s.name for s in _scenes]
    return {_names[0]: True}

def check_valid_viirs_missing(token, prod_name_list):
    _scenes = Scene.where({"status":"submitted", "sensor_type":"viirs"})
    _names = [s.name for s in _scenes]
    return {_names[0]: False}

def get_user_name(token, contactid, ipaddr):
    return 'klmsith@usgs.gov'

def get_order_status(token, tramid):
    response = None
    if tramid == sample_tram_order_ids()[0]:
        response = {'units': [{'orderingId':sample_scene_names()[0], 'statusCode': 'R'}]}
    elif tramid == sample_tram_order_ids()[1]:
        response = {'units': [{'orderingId':sample_scene_names()[1], 'statusCode': 'C'}]}
    elif tramid == sample_tram_order_ids()[2]:
        response = {'units': [{'orderingId':sample_scene_names()[2], 'statusCode': 'R'}]}
    else:
        response = {'units': [{'orderingId': sample_scene_names()[0], 'statusCode': 'C'}]}
    return response

def update_order_status(token, ee_order_id, ee_unit_id, something):
    return True, True, True


def update_order_status_fail(token, ee_order_id, ee_unit_id, something):
    raise Exception('lta comms failed')

def sample_tram_order_ids():
    return '0611512239617', '0611512239618', '0611512239619'

def sample_scene_names():
    return 'LC81370432014073LGN00', 'LC81390422014071LGN00', 'LC81370422014073LGN00'

def get_available_orders_partial(token, contactid, partial=False):
    units = [{u'datasetName': None,
              u'displayId': None,
              u'entityId': None,
              u'orderingId': u'LT05_L1GS_125061_19871229_20170210_01_T2',
              u'productCode': u'SR05',
              u'productDescription': u'LANDSAT TM COLLECTIONS LAND SURFACE REFLECTANCE ON-DEMAND',
              u'statusCode': None,
              u'statusText': None,
              u'unitNumber': 1}]

    ret = [{u'contactId': contactid,
            u'orderNumber': u'0101905173361',
            u'statusCode': u'Q',
            u'statusText': u'Queued for Processing',
            u'units': units}]

    if partial:
        units.append({u'datasetName': None,
                      u'displayId': None,
                      u'entityId': None,
                      u'orderingId': u'LT05_L1TP_025027_20110913_20160830_01_T1',
                      u'productCode': u'SR05',
                      u'productDescription': u'LANDSAT TM COLLECTIONS LAND SURFACE REFLECTANCE ON-DEMAND',
                      u'statusCode': None,
                      u'statusText': None,
                      u'unitNumber': 2})

        ret = [{u'contactId': contactid,
                u'orderNumber': u'0101905173361',
                u'statusCode': u'Q',
                u'statusText': u'Queued for Processing',
                u'units': units}]

    return ret
