'''
Purpose: ERS API client module
Author: Clay Austin
'''
from api.system.logger import ilogger as logger

import requests
from api.providers.configuration.configuration_provider import ConfigurationProvider

cfg = ConfigurationProvider()


class ERSApiErrorException(Exception):
    pass


class ERSApiConnectionException(Exception):
    pass


class ERSApiAuthFailedException(Exception):
    pass


class ERSApi(object):

    def __init__(self):
        self._host = cfg.url_for('ersapi')
        self._secret = cfg.get("ers.%s.secret" % cfg.mode)

    def _api(self, verb, url, data=None, header=None):
        # certificate verification fails in dev/tst
        verify = True if cfg.mode == 'ops' else False
        try:
            logger.debug('[%s] %s', verb.upper(), self._host+url)
            resp = getattr(requests, verb)(self._host + url, data=data,
                                           headers=header, verify=verify)
            resp.raise_for_status()
        except Exception as e:
            raise ERSApiConnectionException(e)
        try:
            data = resp.json()
        except Exception as e:
            raise ERSApiErrorException(e)
        return data

    def _api_post(self, url, data):
        return self._api('post', url, data=data)

    def _api_get(self, url, header):
        return self._api('get', url, header=header)

    def get_user_info(self, user, passw):
        """ Handles the authentication with ERS, and gets the users information

        The information used are:
            {"username", "firstName", "lastName", "email", "contact_id"}

        :param user: ERS username
        :param passw: ERS password
        :return: dict
        """
        if passw:
            auth_resp = self._api_post('/auth', {'username': user,
                                                 'password': passw,
                                                 'client_secret': self._secret})
        else:
            auth_resp = {'data': {'authToken': user}, 'errors': None}

        if not auth_resp['errors']:
            headers = {'X-AuthToken': auth_resp['data']['authToken']}
            user_resp = self._api_get('/me', headers)
            if not user_resp['errors']:
                return user_resp['data']
            else:
                msg = ('Error retrieving user {} details. message {}'
                       .format(user, user_resp['errors']))
                raise ERSApiErrorException(msg)
        else:
            msg = ('Error authenticating {}. message: {}'
                   .format(user, auth_resp['errors']))
            raise ERSApiAuthFailedException(msg)
