# Contains user facing REST functionality
import traceback

import flask
import memcache

from api.interfaces.ordering.version1 import API as APIv1
from api.domain import user_api_operations
from api.system.logger import ilogger as logger
from api.util import api_cfg
from api.util import lowercase_all
from api.domain.user import User, UserException
from api.external.ers import (
    ERSApiErrorException, ERSApiConnectionException, ERSApiAuthFailedException)
from api.transports.http_json import (
    MessagesResponse, UserResponse, OrderResponse, OrdersResponse)
from api import ValidationException, InventoryException

from flask import jsonify
from flask import make_response
from flask import request
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.restful import Resource

from werkzeug.exceptions import BadRequest

from functools import wraps

espa = APIv1()
auth = HTTPBasicAuth()
cache = memcache.Client(['127.0.0.1:11211'], debug=0)

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


def greylist(func):
    """
    Provide a decorator to enact black and white lists on user endpoints

    References http://flask.pocoo.org/docs/0.11/deploying/wsgi-standalone/#proxy_setups
    and http://github.com/mattupsate/flask-security
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        black_ls = api_cfg().get('user_blacklist')
        white_ls = api_cfg().get('user_whitelist')
        denied_response = MessagesResponse(errors=['Access Denied'],
                                           code=403)
        remote_addr = user_ip_address()
        # prohibited ip's
        if black_ls:
            if remote_addr in black_ls.split(','):
                return denied_response()

        # for when were guarding access
        if white_ls:
            if remote_addr not in white_ls.split(','):
                return denied_response()

        return func(*args, **kwargs)
    return decorated


def version_filter(func):
    """
    Provide a decorator to enact a version filter on all endpoints
    """
    def decorated(*args, **kwargs):
        versions = user_api_operations.keys()
        url_version = request.url.split('/')[4].replace('v', '')
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
    reasons = ['unknown', 'auth', 'conn']
    reason = flask.g.get('error_reason', '')
    if reason not in reasons or reason == 'unknown':
        if reason not in reasons:
            logger.debug('ERR uncaught exception in user authentication')
        msg = MessagesResponse(errors=["System experienced an exception. "
                                       "Admins have been notified"],
                               code=500)
    elif reason == 'auth':
        msg = MessagesResponse(errors=['Invalid username/password'],
                               code=401)
    elif reason == 'conn':
        msg = MessagesResponse(warnings=['ERS connection failed'],
                               code=503)
    return msg()


@auth.verify_password
def verify_user(username, password):
    try:
        # usernames with spaces are valid in EE, though they can't be used for cache keys
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
        flask.g.user = user  # Replace usage with cached version
    except UserException as e:
        logger.info('Invalid login attempt, username: {}, {}'.format(username, e))
        flask.g.error_reason = 'unknown'
        return False
    except ERSApiAuthFailedException as e:
        logger.info('Invalid login attempt, username: {}, {}'.format(username, e))
        flask.g.error_reason = 'auth'
        return False
    except ERSApiErrorException as e:
        logger.info('ERS lookup failed, username: {}, {}'.format(username, e))
        flask.g.error_reason = 'unknown'
        return False
    except ERSApiConnectionException as e:
        logger.info('ERS is down {}'.format(e))
        flask.g.error_reason = 'conn'
        return False
    except Exception:
        logger.info('Invalid login attempt, username: {}'.format(username))
        flask.g.error_reason = 'unknown'
        return False

    return True


class Index(Resource):
    decorators = [greylist]

    @staticmethod
    def get():
        return 'Welcome to the ESPA API, please direct requests to /api'


class VersionInfo(Resource):
    decorators = [auth.login_required, greylist]

    def get(self, version=None):
        info_dict = user_api_operations

        if version:
            if version in info_dict:
                response = info_dict[version]
                return_code = 200
            else:
                ver_str = ", ".join(info_dict.keys())
                msg = "Invalid api version {0}. Options: {1}".format(version, ver_str)
                response = MessagesResponse(errors=[msg], code=404)
        else:
            response = espa.api_versions()
            return_code = 200

        return response()


class AvailableProducts(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version, prod_id=None):
        if prod_id is None:
            prod_list = request.get_json(force=True)['inputs']
        if prod_id:
            prod_list = [prod_id]
        return espa.available_products(prod_list, auth.username())


class ListOrders(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version, email=None):
        try:
            filters = request.get_json(force=True)
        except BadRequest as e:
            # no json this time # FIXME: Should this fail?
            filters = {}

        if email:
            search = dict(email=str(email), filters=filters)
        else:
            search = dict(username=auth.username(), filters=filters)
        response = OrdersResponse(espa.fetch_user_orders(**search))
        response.limit = ('orderid',)
        response.code = 200
        return response()


class ValidationInfo(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version):
        param = request.url
        response = None

        if 'projections' in param:
            response = espa.validation.fetch_projections()
        elif 'formats' in param:
            response = espa.validation.fetch_formats()
        elif 'resampling-methods' in param:
            response = espa.validation.fetch_resampling()
        elif 'order-schema' in param:
            response = espa.validation.fetch_order_schema()

        return response


class Ordering(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version, ordernum):
        user = flask.g.user
        order = espa.fetch_order(ordernum)
        response = OrderResponse(**order.as_dict())
        response.code = 200
        if 'order-status' in request.url:
            response.limit = ('orderid', 'status')
        else:
            if not user.is_staff:
                response.limit = ('orderid','order_date','completion_date',
                                  'status', 'note', 'order_source',
                                  'product_opts')
        return response()


    @staticmethod
    def post(version):
        user = flask.g.user
        message = None
        try:
            order = request.get_json(force=True)
            if order:
                try:
                    order = lowercase_all(order)
                    order = espa.place_order(order, user)
                    message = OrderResponse(**order.as_dict())
                    message.limit = ('orderid', 'status')
                    message.code = 201
                except ValidationException as e:
                    logger.info('Invalid order received: {0}\nresponse {1}'
                                .format(order, e.response))
                    message = MessagesResponse(errors=[e.response],
                                               code=400)
                except InventoryException as e:
                    logger.info('Requested inputs not available: {0}\n'
                                'response {1}'.format(order, e.response))
                    message = MessagesResponse(errors=[e.response],
                                               code=400)
                except Exception as e:
                    logger.debug("exception posting order: {0}\n"
                                 "user: {1}\n msg: {2}\n trace: {3}"
                                 .format(order, user.username, e.message,
                                         traceback.format_exc()))
                    msg = ("System experienced an exception. "
                           "Admins have been notified")
                    message = MessagesResponse(errors=[msg],
                                               code=500)
        except BadRequest as e:
            # request.get_json throws a BadRequest
            logger.debug("BadRequest, could not parse request into json {}\n"
                         "user: {}\nform data {}\n"
                         .format(e.description, user.username, request.form))
            message = MessagesResponse(errors=['Could not parse request into JSON'],
                                       code=400)
        except Exception as e:
            logger.debug("ERR posting order. user: {0}\n error: {1}"
                         .format(user.username, e))
            msg = ("System experienced an exception. "
                   "Admins have been notified")
            message = MessagesResponse(errors=[msg], code=500)

        return message()

    @staticmethod
    def put(version):
        user = flask.g.user
        remote_addr = user_ip_address()
        message = MessagesResponse(errors=["BadRequest"],
                                   code=400)
        update = request.get_json()
        try:
            assert(user.is_staff())  # TODO: plan to be public facing
            order = espa.fetch_order(update.get('orderid'))
            assert(order.user_id == user.id)
            order = espa.cancel_order(order.id, remote_addr)
            assert(order.status == 'cancelled')
            message = OrderResponse(**order.as_dict())
            message.limit = ('orderid', 'status')
            message.code = 202
        except BadRequest as e:
            pass
        except Exception as e:
            logger.debug("ERR cancelling order. user: {0}\n error: {1}"
                         .format(user.username, e))
            msg = ("System experienced an exception. "
                   "Admins have been notified")
            message = MessagesResponse(errors=[msg], code=500)

        return message()


class UserInfo(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version):
        user = UserResponse(**flask.g.user.as_dict())
        user.code = 200
        return user()


class ItemStatus(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version, orderid, itemnum='ALL'):
        user = flask.g.user
        return espa.item_status(orderid, itemnum, user.username)


class BacklogStats(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version):
        return espa.get_backlog()


class PublicSystemStatus(Resource):
    decorators = [auth.login_required, greylist, version_filter]

    @staticmethod
    def get(version):
        return espa.get_system_status()