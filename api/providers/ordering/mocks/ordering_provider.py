class MockOrderingProvider(object):

    def fetch_user_orders(self, username='', email='', filters={}):
        orders = ['1', '2']
        return orders
