import datetime
import os

from api.domain import sensor
from api.domain.order import Order
from api.domain.scene import Scene
from api.domain.user import User
from api.util.dbconnect import db_instance
from api.util import julian_date_check
from api.providers.ordering import ProviderInterfaceV0
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.providers.caching.caching_provider import CachingProvider
# ----------------------------------------------------------------------------------
from api.external import lta, onlinecache  # TODO: is this the best place for these?
from api.notification import emails        # TODO: is this the best place for these?
from api.system.logger import ilogger as logger  # TODO: is this the best place for these?

import copy
import yaml

cache = CachingProvider()
config = ConfigurationProvider()
from api import __location__


class OrderingProviderException(Exception):
    pass


class OrderingProvider(ProviderInterfaceV0):
    @staticmethod
    def sensor_products(product_id):
        # coming from uwsgi, product_id is unicode
        if isinstance(product_id, basestring):
            prod_list = product_id.split(",")
        else:
            prod_list = product_id

        return sensor.available_products(prod_list)

    def available_products(self, product_id, username):
        """
        Check to see what products are available to user based on
        an input list of scenes

        :param product_id: list of desired inputs
        :param username: username
        :return: dictionary
        """
        user = User.by_username(username)
        pub_prods = copy.deepcopy(OrderingProvider.sensor_products(product_id))

        with open(os.path.join(__location__, 'domain/restricted.yaml')) as f:
                restricted = yaml.safe_load(f.read())

        role = False if user.is_staff() else True

        restrict_all = restricted.get('all', {})
        all_role = restrict_all.get('role', [])
        all_by_date = restrict_all.get('by_date', {})
        all_ordering_rsctd = restrict_all.get('ordering', [])

        upd = {'date_restricted': {}, 'ordering_restricted': {}}
        for sensor_type, prods in pub_prods.items():
            if sensor_type == 'not_implemented':
                continue

            stype = sensor_type.replace('_collection', '') if '_collection' in sensor_type else sensor_type

            sensor_restr = restricted.get(stype, {})
            role_restr = sensor_restr.get('role', []) + all_role
            by_date_restr = sensor_restr.get('by_date', {})

            # All overrides any sensor related dates
            by_date_restr.update(all_by_date)

            outs = pub_prods[sensor_type]['products']
            ins = pub_prods[sensor_type]['inputs']

            if sensor_type in all_ordering_rsctd:
                for sc_id in ins:
                    if sensor_type in upd['ordering_restricted']:
                        upd['ordering_restricted'][sensor_type].append(sc_id)
                    else:
                        upd['ordering_restricted'][sensor_type] = [sc_id]
                pub_prods.pop(sensor_type)
                continue

            remove_me = []
            if role:
                for prod in role_restr:
                    try:
                        outs.remove(prod)
                    except ValueError:
                        continue

            for prod in outs:
                if prod in by_date_restr:
                    r = sensor_restr['by_date'][prod]
                    for sc_id in ins:
                        obj = sensor.instance(sc_id)
                        julian = '{}{}'.format(obj.year, obj.doy)

                        if not julian_date_check(julian, r):
                            remove_me.append(prod)

                            if prod in upd['date_restricted']:
                                upd['date_restricted'][prod].append(sc_id)
                            else:
                                upd['date_restricted'][prod] = [sc_id]

            for rem in remove_me:
                try:
                    outs.remove(rem)
                except ValueError:
                    continue

        if upd['date_restricted']:
            pub_prods.update(date_restricted=upd['date_restricted'])
        if upd['ordering_restricted']:
            pub_prods.update(ordering_restricted=upd['ordering_restricted'])

        return pub_prods

    def fetch_user_orders(self, username='', email='', user_id='', filters=None):

        if filters and not isinstance(filters, dict):
            raise OrderingProviderException('filters must be dict')

        if username:
            usearch = {'username': username}
        elif email:
            usearch = {'email': email}
        elif user_id:
            usearch = {'id': user_id}

        user = User.where(usearch)
        if len(user) != 1:
            return list()
        else:
            user = user.pop()

        if filters:
            params = dict(filters)
            params.update({'user_id': user.id})
        else:
            params = {'user_id': user.id}

        resp = Order.where(params)
        return resp

    def fetch_order(self, ordernum):
        orders = Order.where({'orderid': ordernum})
        return orders

    def place_order(self, new_order, user):
        """
        Build an order dictionary to be place into the system

        :param new_order: dictionary representation of the order received
        :param user: user information associated with the order
        :return: orderid to be used for tracking
        """
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

        order_dict = {'orderid': Order.generate_order_id(user.email),
                      'user_id': user.id,
                      'order_type': 'level2_ondemand',
                      'status': 'ordered',
                      'product_opts': new_order,
                      'ee_order_id': '',
                      'order_source': 'espa',
                      'order_date': ts,
                      'priority': 'normal',
                      'note': new_order.get('note', None),
                      'email': user.email,
                      'product_options': ''}

        result = Order.create(order_dict)
        return result

    def cancel_order(self, orderid, request_ip_address):
        """
        Cancels an order, and all scenes contained within it

        :return:
        """
        order = Order.where({'id': orderid})
        if len(order) != 1:
            raise OrderingProviderException('Order not found')
        else:
            order = order.pop()

        logger.info('Received request to cancel {} from {}'
                    .format(orderid, request_ip_address))
        killable_scene_states = ('submitted', 'oncache', 'onorder', 'queued',
                                 'retry', 'error', 'unavailable', 'complete')
        scenes = order.scenes(sql_dict={'status': killable_scene_states})
        if len(scenes) > 0:
            Scene.bulk_update([s.id for s in scenes], Scene.cancel_opts())
        else:
            logger.info('No scenes to cancel for order {}'
                        .format(orderid, request_ip_address))

        order.status = 'cancelled'
        order.save()
        logger.info('Request to cancel {} from {} successful.'
                    .format(orderid, request_ip_address))
        return order

    def item_status(self, orderid, itemid='ALL', username=None, filters=None):
        user = User.by_username(username)

        if not isinstance(filters, dict):
            if filters is None:
                filters = dict()
            else:
                raise TypeError('supplied filters invalid')

        if orderid:
            orders = Order.where({'orderid': orderid})
        else:
            orders = Order.where({'user_id': user.id})

        search = dict()
        if 'status' in filters:
            search.update(status=(filters.get('status'),))

        if 'name' in filters:
            search.update(name=(filters.get('name'),))
        elif itemid is not "ALL":
            search.update(name=(itemid,))

        response = dict()
        for order in orders:
            response[order.orderid] = order.scenes(search)
        return response

    def get_system_status(self):
        sql = "select key, value from ordering_configuration where " \
              "key in ('msg.system_message_body', 'msg.system_message_title', 'system.display_system_message');"
        with db_instance() as db:
            db.select(sql)

        if db:
            resp_dict = dict(db.fetcharr)
            return {'system_message_body': resp_dict['msg.system_message_body'],
                    'system_message_title': resp_dict['msg.system_message_title'],
                    'display_system_message': resp_dict['system.display_system_message']}
        else:
            return {'system_message_body': None, 'system_message_title': None}
