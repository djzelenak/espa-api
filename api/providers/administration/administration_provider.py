
from api.providers.administration import AdminProviderInterfaceV0
from api.providers.administration import AdministrationProviderException
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.external.onlinecache import OnlineCache
from api.system.logger import ilogger as logger
from api.util.dbconnect import db_instance
from api.util.dbconnect import DBConnectException
from api.domain.order import Order
from api.domain.scene import SceneException, Scene
from api.util import api_cfg


class AdministrationProvider(AdminProviderInterfaceV0, metaclass=AdminProviderInterfaceV0):
    config = ConfigurationProvider()
    db = db_instance()

    def orders(self, query=None, cancel=False):
        pass

    def system(self, key=None, disposition='on'):
        pass

    def products(self, query=None, resubmit=None):
        pass

    def access_configuration(self, key=None, value=None, delete=False):
        if not key:
            return self.config.configuration_keys
        elif not delete and not value:
            return self.config.get(key)
        elif value and not delete:
            return self.config.put(key, value)
        elif delete and key:
            return self.config.delete(key)

    # def restore_configuration(self, filepath, clear=False):
    def restore_configuration(self, filepath):
        # self.config.load(filepath, clear=clear)
        self.config.load(filepath)

    def backup_configuration(self, path=None):
        return self.config.dump(path)

    def onlinecache(self, list_orders=False, orderid=None, filename=None, delete=False):
        if delete and orderid and filename:
            return OnlineCache().delete(orderid, filename)
        elif delete and orderid:
            return OnlineCache().delete(orderid)
        elif list_orders:
            return OnlineCache().list()
        elif orderid:
            return OnlineCache().list(orderid)
        else:
            return OnlineCache().capacity()

    @staticmethod
    def error_to(orderid, state):
        order = Order.find(orderid)
        err_scenes = order.scenes({'status': 'error'})
        try:
            if state == 'submitted':
                Scene.bulk_update([s.id for s in err_scenes], {'status': state,
                                                               'orphaned': None,
                                                               'reported_orphan': None,
                                                               'log_file_contents': '',
                                                               'note': '',
                                                               'retry_count': 0})

                order.status = 'ordered'
                order.completion_email_sent = None
                order.save()

            else:
                Scene.bulk_update([s.id for s in err_scenes], {'status': state})

            return True
        except SceneException as e:
            num, message = e.args
            logger.critical('ERR admin provider error_to\ntrace: {}'.format(message))
            raise AdministrationProviderException('ERR updating with error_to')

    @staticmethod
    def get_system_status():
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

    @staticmethod
    def update_system_status(params):

        if set(params) != {'system_message_title', 'system_message_body', 'display_system_message'}:
            return {'msg': 'Only 3 params are valid, and they must be present:'
                           'system_message_title, system_message_body,'
                           'display_system_message'}

        sql = '''update ordering_configuration set value = %s where key = 'msg.system_message_title';
                 update ordering_configuration set value = %s where key = 'msg.system_message_body';
                 update ordering_configuration set value = %s where key = 'system.display_system_message'; '''
        sql_vals = (params['system_message_title'], params['system_message_body'], params['display_system_message'])
        try:
            with db_instance() as db:
                db.execute(sql, sql_vals)
                db.commit()
        except DBConnectException as e:
            num, message = e.args
            logger.critical("error updating system status: {}".format(e))
            return {'msg': "error updating database: {}".format(message)}

        return True

    @staticmethod
    def get_system_config():
        return ConfigurationProvider().retrieve_config()

    @staticmethod
    def admin_whitelist():
        return api_cfg()['admin_whitelist']

    @staticmethod
    def stat_whitelist():
        return api_cfg()['stat_whitelist']
