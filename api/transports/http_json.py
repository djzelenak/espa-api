"""
    Purpose: Force consistent JSON response objects
"""
import json
import datetime

from flask import make_response, jsonify


class SchemaDefinitionResponse(object):
    def __init__(self):  # FIXME: this is currently not used
        self.projections = None
        self.formats = None
        self.resampling = None
        self.products = None
        self.versions = None


class UserResponse(object):
    def __init__(self, email, first_name, last_name, roles, username, code=None):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.roles = roles
        self.username = username
        self.code = code

    def __repr__(self):
        return repr(self.as_json())

    def __call__(self):
        if self.code is None:
            raise ValueError('UserResponse must set response_code')
        return make_response(jsonify(self.as_json()), self.code)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Email must be a string')
        self._email = value

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        if not isinstance(value, basestring):
            raise TypeError('First Name must be a string')
        self._first_name = value

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Last Name must be a string')
        self._last_name = value

    @property
    def roles(self):
        return self._roles

    @roles.setter
    def roles(self, value):
        if not isinstance(value, list):
            raise TypeError('Roles are always a list')
        if len(value):
            if not all(isinstance(v, basestring) for v in value):
                raise TypeError('Roles must all be strings')
        self._roles = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Username must be a string')
        self._username = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        valid_codes = (200, 201)
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('HTTP Response Code is always an integer')
            if value not in valid_codes:
                raise TypeError('HTTP Response Code must be one of: {}'
                                .format(valid_codes))
        self._code = value

    def as_json(self):
        """ Removes the leading underscore used in validation
        :return: str
        """
        return {"email": self.email,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "roles": self.roles,
                "username": self.username
                }


class SceneResponse(object):
    def __init__(self, name, note, status, completion_date, cksum_download_url,
                 product_dload_url, log_file_contents, id):
        self.name = name
        self.note = note
        self.status = status
        self.completion_date = completion_date
        self.cksum_download_url = cksum_download_url
        self.product_dload_url = product_dload_url
        self.log_file_contents = log_file_contents
        self.id = id

    def __repr__(self):
        return str(self.as_json())

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._name = value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if not isinstance(value, int):
            raise TypeError('Expected integer')
        self._id = value

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._note = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._status = value

    @property
    def completion_date(self):
        return self._completion_date

    @completion_date.setter
    def completion_date(self, value):
        if isinstance(value, datetime.datetime):
                value = str(value)
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._completion_date = value

    @property
    def cksum_download_url(self):
        return self._cksum_download_url

    @cksum_download_url.setter
    def cksum_download_url(self, value):
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._cksum_download_url = value

    @property
    def product_dload_url(self):
        return self._product_dload_url

    @product_dload_url.setter
    def product_dload_url(self, value):
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._product_dload_url = value

    @property
    def log_file_contents(self):
        return self._log_file_contents

    @log_file_contents.setter
    def log_file_contents(self, value):
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._log_file_contents = value

    def as_dict(self):
        return {"cksum_download_url": self.cksum_download_url,
                "completion_date": self.completion_date,
                "name": self.name,
                "note": self.note,
                "product_dload_url": self.product_dload_url,
                "status": self.status,
                "log_file_contents": self.log_file_contents,
                "id": self.id}


class ItemsResponse(object):
    def __init__(self, orders, limit=None, code=None):
        self.orders = orders
        self.limit = limit
        self.code = code

    def __repr__(self):
        return repr(self.as_json())

    def __call__(self):
        if self.code is None:
            raise ValueError('ItemsResponse must set response_code')
        return make_response(jsonify(self.as_json()), self.code)

    @property
    def orders(self):
        return self._orders

    @orders.setter
    def orders(self, value):
        if not isinstance(value, dict):
            raise TypeError('Expected dict')
        if not all([isinstance(v, list) for k, v in value.items()]):
            raise TypeError('Expected dict of lists')
        self._orders = {k: [SceneResponse(**s.as_dict()) for s in v] for k,v in value.items()}

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, value):
        if value and not isinstance(value, tuple):
            raise TypeError('Expected tuple')
        self._limit = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        valid_codes = (200,)
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('HTTP Response Code is always an integer')
            if value not in valid_codes:
                raise TypeError('HTTP Response Code must be one of: {}'
                                .format(valid_codes))
        self._code = value

    def as_json(self):
        resp = {k: [{sk: sv for sk, sv in s.as_dict().items()} for s in v]
                for k, v in self.orders.items()}
        if self.limit:
            resp = {k: [{sk: sv for sk, sv in s.items()
                         if sk in self.limit} for s in v]
                    for k, v in resp.items()}
        return resp


class OrderResponse(object):
    def __init__(self, orderid, status, completion_date, note, order_date,
                 order_source, order_type, priority, product_options,
                 product_opts, products_complete=None, products_error=None,
                 products_ordered=None, limit=None, code=None):
        self.orderid = orderid
        self.status = status
        self.completion_date = completion_date
        self.note = note
        self.order_date = order_date
        self.order_source = order_source
        self.order_type = order_type
        self.priority = priority
        self.product_options = product_options
        self.product_opts = product_opts
        self.products_complete = products_complete
        self.products_error = products_error
        self.products_ordered = products_ordered
        self.limit = limit
        self.code = code

    def __repr__(self):
        return repr(self.as_json())

    def __call__(self):
        if self.code is None:
            raise ValueError('OrderResponse must set response_code')
        return make_response(jsonify(self.as_json()), self.code)

    @property
    def orderid(self):
        return self._orderid

    @orderid.setter
    def orderid(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._orderid = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._status = value

    @property
    def completion_date(self):
        return self._completion_date

    @completion_date.setter
    def completion_date(self, value):
        if isinstance(value, datetime.datetime):
                value = str(value)
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._completion_date = value

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        if value is None:
            value = ''
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._note = value

    @property
    def order_date(self):
        return self._order_date

    @order_date.setter
    def order_date(self, value):
        if isinstance(value, datetime.datetime):
                value = str(value)
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._order_date = value

    @property
    def order_source(self):
        return self._order_source

    @order_source.setter
    def order_source(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._order_source = value

    @property
    def order_type(self):
        return self._order_type

    @order_type.setter
    def order_type(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._order_type = value

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._priority = value

    @property
    def product_options(self):  # FIXME: IS THIS USEFUL?
        return self._product_options

    @product_options.setter
    def product_options(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._product_options = value

    @property
    def product_opts(self):
        return self._product_opts

    @product_opts.setter
    def product_opts(self, value):
        if not isinstance(value, dict):
            raise TypeError('Expected Dictionary')
        self._product_opts = value

    @property
    def products_complete(self):
        return self._products_complete

    @products_complete.setter
    def products_complete(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('Expected Integer')
        self._products_complete = value

    @property
    def products_error(self):
        return self._products_error

    @products_error.setter
    def products_error(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('Expected Integer')
        self._products_error = value

    @property
    def products_ordered(self):
        return self._products_ordered

    @products_ordered.setter
    def products_ordered(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('Expected Integer')
        self._products_ordered = value

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, value):
        if value and not isinstance(value, tuple):
            raise TypeError('Expected tuple')
        self._limit = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        valid_codes = (200,  # Order fetch
                       201,  # Order created
                       202,  # Order updated (cancelled)
        )
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('HTTP Response Code is always an integer')
            if value not in valid_codes:
                raise TypeError('HTTP Response Code must be one of: {}'
                                .format(valid_codes))
        self._code = value

    def as_json(self):
        resp = {
                  "completion_date": self.completion_date,
                  "note": self.note,
                  "order_date": self.order_date,
                  "order_source": self.order_source,
                  "order_type": self.order_type,
                  "orderid": self.orderid,
                  "priority": self.priority,
                  "product_options": self.product_options,
                  "product_opts": self.product_opts,
                  "status": self.status
                }
        if self.limit:
            resp = {k: resp.get(k) for k in self.limit}
        return resp


class OrdersResponse(object):
    def __init__(self, orders, limit=None, code=None):
        self.orders = orders
        self.limit = limit
        self.code = code

    def __repr__(self):
        return repr(self.as_list())

    def __call__(self):
        if self.code is None:
            raise ValueError('OrdersResponse must set response_code')
        return make_response(json.dumps(self.as_list()), self.code)

    @property
    def orders(self):
        return self._orders

    @orders.setter
    def orders(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected List')
        if not all([isinstance(i, OrderResponse) for i in value]):
            value = map(lambda x: OrderResponse(**x.as_dict()), value)
        self._orders = value

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, value):
        if value and not isinstance(value, tuple):
            raise TypeError('Expected tuple')
        self._limit = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        valid_codes = (200, 201)
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('HTTP Response Code is always an integer')
            if value not in valid_codes:
                raise TypeError('HTTP Response Code must be one of: {}'
                                .format(valid_codes))
        self._code = value

    def as_list(self):
        mapper = lambda x: {"order_note": x.note,
                            "order_status": x.status,
                            "orderid": x.orderid}
        resp = map(mapper, self.orders)

        if self.limit:
            if len(self.limit) > 1:
                resp = [{k: getattr(r, k) for k in self.limit} for r in resp]
            else:
                resp = [getattr(o, self.limit[0]) for o in self.orders]
        return resp


class MessagesResponse(object):
    def __init__(self, errors=None, warnings=None, code=None):
        self.errors = errors or list()
        self.warnings = warnings or list()
        self.code = code

    def __repr__(self):
        return repr(self.as_json())

    def __call__(self):
        if self.code is None:
            if len(self.errors):
                self.code = 500
            elif len(self.warnings):
                self.code = 200
        return make_response(jsonify(self.as_json()), self.code)

    @property
    def errors(self):
        return self._errors

    @errors.setter
    def errors(self, value):
        if not isinstance(value, list):
            raise TypeError('Errors is always a list')
        if len(value):
            if not all(isinstance(v, (basestring, dict)) for v in value):
                raise TypeError('Errors must all be strings or dictionaries')
        self._errors = value

    @property
    def warnings(self):
        return self._warnings

    @warnings.setter
    def warnings(self, value):
        if not isinstance(value, list):
            raise TypeError('Warnings is always a list')
        if len(value):
            if not all(isinstance(v, basestring) for v in value):
                raise TypeError('Warnings must all be strings')
        self._warnings = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        valid_codes = (200,  # Warnings
                       400,  # Bad JSON supplied
                       401,  # Auth Failed
                       403,  # Forbidden (Blacklist)
                       404,  # URL Not found
                       405,  # Bad HTTP Method
                       500,  # Uncaught Error
                       503   # Service Unavailable (probably handled by proxy)
        )
        if value is not None:
            if not isinstance(value, int):
                raise TypeError('HTTP Response Code is always an integer')
            if value not in valid_codes:
                raise TypeError('HTTP Response Code must be one of: {}'
                                .format(valid_codes))
        self._code = value

    def as_json(self):
        """ Ensure that errors always supersede warnings (strip hidden)
        :return: str
        """
        resp = dict()
        if self.errors or self.warnings:
            resp['messages'] = dict()
        if self.errors:  # Errors always supersede warnings
            resp['messages']['errors'] = self.errors
        elif self.warnings:
            resp['messages']['warnings'] = self.warnings
        return resp


BadRequestResponse = MessagesResponse(errors=['Could not parse request into JSON'],
                                      code=400)
SystemErrorResponse = MessagesResponse(errors=["System experienced an exception. "
                                               "Admins have been notified"],
                                       code=500)
AccessDeniedResponse = MessagesResponse(errors=['Access Denied'],
                                        code=403)
AuthFailedResponse = MessagesResponse(errors=['Invalid username/password'],
                                      code=401)
# flask-restful otherwise overrides and handles 405 responses
BadMethodResponse = MessagesResponse(errors=['Invalid method. Try GET instead'],
                                      code=405)