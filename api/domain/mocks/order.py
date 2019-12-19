from api.util.dbconnect import db_instance
from api.domain.order import Order
from api.domain.scene import Scene
from api.domain.user import User
from api.util import chunkify, conv_dict, jsonify
from test.version0_testorders import build_base_order
from api.providers.ordering.ordering_provider import OrderingProvider
from api.providers.production.production_provider import ProductionProvider
from api.external.mocks import inventory as mock_inventory
import os
import random
import datetime
import json


class MockOrderException(Exception):
    pass


class MockOrder(object):
    """ Class for interacting with the ordering_order table """

    def __init__(self):
        try:
            mode = os.environ["espa_api_testing"]
            if mode != "True":
                raise MockOrderException("MockOrder objects only allowed while testing")
        except Exception:
            raise MockOrderException("MockOrder objects only allowed while testing")
        self.base_order = build_base_order()
        self.ordering_provider = OrderingProvider()
        self.production_provider = ProductionProvider()

    def __repr__(self):
        return "MockOrder:{0}".format(self.__dict__)

    def as_dict(self):
        return {
            "completion_date": '',
            "note": '',
            "order_date": '',
            "order_source": '',
            "order_type": '',
            "orderid": '',
            "priority": '',
            "product_options": '',
            "product_opts": '',
            "status": ''
        }

    def generate_testing_order(self, user_id):
        user = User.find(user_id)
        # need to monkey with the email, otherwise we get collisions with each
        # test creating a new scratch order with the same user
        rand = str(random.randint(1, 99))
        user.email = rand + user.email
        order = self.ordering_provider.place_order(self.base_order, user)
        return order.id

    def generate_ee_testing_order(self, user_id, partial=False):
        # Have to emulate a bunch of load_ee_orders

        ee_orders = (conv_dict(m) for m in mock_inventory.get_available_orders_partial('fauxtoken', partial))
        email_addr = 'klsmith@usgs.gov'
        order = None
        for eeorder in ee_orders:
            order_id = Order.generate_ee_order_id(email_addr, eeorder.get('orderNumber'))
            units = jsonify(eeorder.get('units'))
            scene_info = [conv_dict(u) for u in units]
            user = User.find(user_id)
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

            order_dict = {'orderid': order_id,
                          'user_id': user.id,
                          'order_type': 'level2_ondemand',
                          'status': 'ordered',
                          'note': 'EarthExplorer order id: {}'.format(eeorder.get('orderNumber')),
                          'ee_order_id': eeorder.get('orderNumber'),
                          'order_source': 'ee',
                          'order_date': ts,
                          'priority': 'normal',
                          'email': user.email,
                          'product_options': 'include_sr: true',
                          'product_opts': Order.get_default_ee_options(scene_info)}

            order = Order.create(order_dict)
            self.production_provider.load_ee_scenes(scene_info, order.id)

        try:
            return order.id
        except AttributeError:
            raise MockOrderException("The Order object is None or is missing an ID attribute")

    def scene_names_list(self, order_id):
        scenes = Scene.where({'order_id': order_id})
        names_list = [s.name for s in scenes]
        return names_list

    def tear_down_testing_orders(self):
        # delete scenes first
        scene_sql = "DELETE FROM ordering_scene where id > 0;"
        with db_instance() as db:
            db.execute(scene_sql)
            db.commit()
        # now you can delete orders
        ord_sql = "DELETE FROM ordering_order where id > 0;"
        with db_instance() as db:
            db.execute(ord_sql)
            db.commit()
        return True

    def update_scenes(self, order_id, stype, attribute, values):
        scenes = Scene.where({'order_id': order_id, 'sensor_type': stype})
        xscenes = chunkify(scenes, len(values))

        for idx, value in enumerate(values):
            for scene in xscenes[idx]:
                scene.update(attribute, value)
        return True

    def names_tuple(self, number, user_id):
        order_id = self.generate_testing_order(user_id)
        order = Order.find(order_id)
        scene_names = [i.name for i in order.scenes()]
        scene_names = scene_names[0:number]
        list_of_tuples = [(order.orderid, s) for s in scene_names]
        return list_of_tuples

    @classmethod
    def place_order(cls, order, user):
        self = MockOrder()
        # need to monkey with the email, otherwise we get collisions with each
        # test creating a new scratch order with the same user
        rand = str(random.randint(1, 99))
        user.email = rand + user.email
        order = self.ordering_provider.place_order(self.base_order, user)
        return order

    @classmethod
    def cancel_order(cls, orderid, request_address):
        order = Order.find(orderid)
        order.status = 'cancelled'
        order.save()
        return order
