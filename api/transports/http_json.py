"""
    Purpose: Force consistent JSON response objects
"""


class SchemaDefinitionResponse(object):
    def __init__(self):  # FIXME: this is currently not used
        self.projections = None
        self.formats = None
        self.resampling = None
        self.products = None
        self.versions = None


class UserResponse(object):
    def __init__(self, email, first_name, last_name, roles, username):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.roles = roles
        self.username = username

    def __repr__(self):
        return repr(self.as_dict())

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

    def as_dict(self):
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
                 product_dload_url):
        self.name = name
        self.note = note
        self.status = status
        self.completion_date = completion_date
        self.cksum_download_url = cksum_download_url
        self.product_dload_url = product_dload_url

    def __repr__(self):
        pass

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._name = value

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
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
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._completion_date = value

    @property
    def cksum_download_url(self):
        return self._cksum_download_url

    @cksum_download_url.setter
    def cksum_download_url(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._cksum_download_url = value

    @property
    def product_dload_url(self):
        return self._product_dload_url

    @product_dload_url.setter
    def product_dload_url(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._product_dload_url = value

    def as_dict(self):
        return {"cksum_download_url": self.cksum_download_url,
                "completion_date": self.completion_date,
                "name": self.name,
                "note": self.note,
                "product_dload_url": self.product_dload_url,
                "status": self.status}


class OrderResponse(object):
    def __init__(self, orderid, status, completion_date, note, order_date,
                 order_source, order_type, priority, product_options,
                 product_opts, products_complete=None, products_error=None,
                 products_ordered=None):
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

    def __repr__(self):
        return repr(self.as_dict())

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
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._completion_date = value

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Expected String')
        self._note = value

    @property
    def order_date(self):
        return self._order_date

    @order_date.setter
    def order_date(self, value):
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

    def as_dict(self):
        return {
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

    def order_status(self):
        """ OrderID and status
        """
        return {"orderid": self.orderid,
                "status": self.status}


class OrdersResponse(object):
    def __init__(self, orders):
        self.orders = orders

    def __repr__(self):
        return repr(self.list_orders())

    @property
    def orders(self):
        return self._orders

    @orders.setter
    def orders(self, value):
        if not isinstance(value, list):
            raise TypeError('Expected List')
        if not all([isinstance(i, Order) for i in value]):
            raise TypeError('Expected List of Orders')
        self._orders = value

    def list_orders(self):
        """  list of orderids
        """
        return {"orders": [o.orderid for o in self.orders]}

    def list_orders_ext(self):
        """ list of order details
        """
        orders = self.orders
        resp = list()
        for o in orders:
            ext_order = {"order_note": o.note,
                         "order_status": o.status,
                         "orderid": o.orderid,
                         "products_complete": o.products_complete,
                         "products_error": o.products_error,
                         "products_ordered": o.products_ordered}
            resp.append(ext_order)
        return resp


class MessagesResponse(object):
    def __init__(self, errors=None, warnings=None):
        self.errors = errors or list()
        self.warnings = warnings or list()

    def __repr__(self):
        return repr(self.as_dict())

    @property
    def errors(self):
        return self._errors

    @errors.setter
    def errors(self, value):
        if not isinstance(value, list):
            raise TypeError('Errors is always a list')
        if len(value):
            if not all(isinstance(v, basestring) for v in value):
                raise TypeError('Errors must all be strings')
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

    def as_dict(self):
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


