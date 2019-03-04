# Contains Admin facing REST functionality

import flask
import memcache
import traceback

from api.domain import default_error_message, admin_api_operations

from api.interfaces.admin.version1 import API as APIv1
from api.system.logger import ilogger as logger
from api.domain.user import User
from api.transports.http_json import MessagesResponse
from api.providers.caching.caching_provider import CachingProvider

from flask import jsonify
from flask import make_response
from flask import request
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource


espa = APIv1()
auth = HTTPBasicAuth()
cache = CachingProvider()


def user_ip_address():
    """
    Try to get the User's originating IP address, across proxies

    :return: string
    """
    is_web_redirect = ('X-Forwarded-For' in request.headers
                       and request.remote_addr == '127.0.0.1')
    if is_web_redirect:
        remote_addr =  request.headers.getlist('X-Forwarded-For'
                                               )[0].rpartition(' ')[-1]
    else:
        remote_addr = request.remote_addr or 'untrackable'
    return remote_addr


def whitelist(func):
    """
    Provide a decorator to enact a white filter on an endpoint

    References http://flask.pocoo.org/docs/0.11/deploying/wsgi-standalone/#proxy_setups
    and http://github.com/mattupsate/flask-security
    """
    def decorated(*args, **kwargs):
        white_ls = espa.get_admin_whitelist()
        denied_response = MessagesResponse(errors=['Access Denied'], code=403)
        remote_addr = user_ip_address()

        if ((remote_addr in white_ls or request.remote_addr in white_ls)
                and remote_addr != 'untrackable'):
            return func(*args, **kwargs)
        else:
            logger.warn('*** Not in whitelist ({1}): {0}'.format(remote_addr, white_ls))
            return denied_response()
    return decorated


def stats_whitelist(func):
    """
    Provide a decorator to whitelist hosts accessing stats
    """
    def decorated(*args, **kwargs):
        white_ls = espa.get_stat_whitelist()
        denied_response = MessagesResponse(errors=['Access Denied'], code=403)
        remote_addr = user_ip_address()

        if ((remote_addr in white_ls or request.remote_addr in white_ls)
                and remote_addr != 'untrackable'):
            return func(*args, **kwargs)
        else:
            logger.warn('*** Not in whitelist ({1}): {0}'.format(remote_addr, white_ls))
            return denied_response()
    return decorated


def version_filter(func):
    """
    Provide a decorator to enact a version filter on all endpoints
    """
    def decorated(*args, **kwargs):
        versions = admin_api_operations.keys()
        url_version = request.url.split('/')[4].replace('v','')
        if url_version in versions:
            return func(*args, **kwargs)
        else:
            msg = MessagesResponse(errors=['Invalid API version {}'
                                           .format(url_version)],
                                   code=404)
            return msg()
    return decorated


@auth.error_handler
def unauthorized():
    msg = MessagesResponse(errors=['Invalid username/password'],
                           code=401)
    return msg()


@auth.verify_password
def verify_user(username, password):
    try:
        cache_key = '{}-credentials'.format(username.replace(' ', '_espa_cred_insert_'))
        cache_entry = cache.get(cache_key)

        if cache_entry:
            # Need to be encrypted?
            if cache_entry['password'] == password:
                user_entry = cache_entry['user_entry']

            # User may have changed their password while it was still cached
            else:
                user_entry = User.get(username, password)
        else:
            user_entry = User.get(username, password)

        cache_entry = {'password': password,
                       'user_entry': user_entry}
        cache.set(cache_key, cache_entry, 7200)

        user = User(*user_entry)
        if not user.is_staff:
            return False
        flask.g.user = user  # Replace usage with cached version
    except Exception:
        logger.info('Invalid login attempt, username: {}'.format(username))
        return False

    return True


class Reports(Resource):
    decorators = [auth.login_required, whitelist, version_filter]

    @staticmethod
    def get(version, name=None, group=None, year=None):
        if 'aux' in request.url:
            return espa.get_aux_report(group, year)
        elif 'report' in request.url:
            if name:
                return espa.get_report(name)
            else:
                return espa.available_reports()
        else:
            # statistics
            if name:
                return espa.get_stat(name)
            else:
                return espa.available_stats()


class ProductionStats(Resource):
    decorators = [version_filter, stats_whitelist]

    @staticmethod
    def get(version, name):
        if 'statistics' in request.url:
            return espa.get_stat(name)
        if 'multistat' in request.url:
            return espa.get_multistat(name)


class SystemStatus(Resource):
    decorators = [auth.login_required, whitelist, version_filter]

    @staticmethod
    def get(version):
        if 'config' in request.url:
            return jsonify(espa.get_system_config())
        else:
            return jsonify(espa.get_system_status())

    @staticmethod
    def post(version):
        data = request.get_json(force=True)
        try:
            response = espa.update_system_status(data)
            if response is not True:
                resp = MessagesResponse(errors=['internal server error'],
                                        code=500)
            elif isinstance(response, dict) and response.keys() == ['msg']:
                resp = MessagesResponse(errors=response['msg'],
                                        code=400)
            else:
                return 'success'
        except Exception as e:
            logger.critical("ERROR updating system status: {0}".format(traceback.format_exc()))
            resp = MessagesResponse(errors=['internal server error'],
                                    code=500)
        return resp()


class OrderResets(Resource):
    decorators = [auth.login_required, whitelist, version_filter]

    @staticmethod
    def put(version, orderid):
        # eg 'error_to_unavailable'
        _to_whole = request.url.split('/')[-2]
        # eg 'unavailable'
        _to_state = _to_whole.split('_')[-1]
        return str(espa.error_to(orderid, _to_state))

