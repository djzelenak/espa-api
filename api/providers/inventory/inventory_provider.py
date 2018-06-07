import os

from api.providers.inventory import InventoryInterfaceV0
from api.external import inventory, lpdaac
from api import InventoryException, InventoryConnectionException
from api.domain import sensor
from api.system.logger import ilogger as logger
from api.providers.configuration.configuration_provider import ConfigurationProvider

config = ConfigurationProvider()


class InventoryProviderV0(InventoryInterfaceV0):
    """
    Check incoming orders against supported inventories

    Raises InventoryException if a requested L1 product is
    unavailable for processing
    """
    def check(self, order, contactid=None):
        ids = sensor.SensorCONST.instances.keys()

        lta_ls = []
        lpdaac_ls = []
        results = {}
        for key in order:
            l1 = ''
            if key in ids:
                inst = sensor.instance(order[key]['inputs'][0])
                l1 = inst.l1_provider

            if l1 == 'dmid':
                lta_ls.extend(order[key]['inputs'])
            elif l1 == 'lpdaac':
                lpdaac_ls.extend(order[key]['inputs'])

        if lta_ls:
            if inventory.available():
                results.update(self.check_dmid(lta_ls, contactid))
            else:
                msg = 'Could not connect to Landsat data source'
                raise InventoryConnectionException(msg)
        if lpdaac_ls:
            if inventory.available():
                results.update(self.check_dmid(lpdaac_ls, contactid))
            elif lpdaac.check_lpdaac_available():
                results.update(self.check_LPDAAC(lpdaac_ls))
            else:
                msg = 'Could not connect to MODIS data source'
                raise InventoryConnectionException(msg)

        not_avail = []
        for key, val in results.items():
            if not val:
                not_avail.append(key)

        if not_avail:
            raise InventoryException(not_avail)

    @staticmethod
    def check_dmid(prod_ls, contactid=None):
        try:
            token = inventory.get_cached_session()
            return inventory.check_valid(token, prod_ls)
        except Exception as e:
            msg = 'Could not connect to EarthExplorer source'
            logger.critical(msg + str(e))
            raise InventoryConnectionException(msg)

    @staticmethod
    def check_LPDAAC(prod_ls):
        return lpdaac.verify_products(prod_ls)


class InventoryProvider(InventoryProviderV0):
    pass


class MockInventoryProvider(InventoryInterfaceV0):
    def check(self, order):
        pass
