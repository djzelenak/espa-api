from api.providers.inventory import InventoryInterfaceV0

from api.external import lta, inventory, lpdaac, nlaps
from api import InventoryException, InventoryConnectionException
from api.domain import sensor


class InventoryProviderV0(InventoryInterfaceV0):
    """
    Check incoming orders against supported inventories

    Raises InventoryException if a requested L1 product is
    unavailable for processing
    """
    def check(self, order, contactid):
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
            if os.getenv('ESPA_M2M_MODE') == 'True':
                results.update(self.check_dmid(lta_ls, contactid))
            else:
                if not lta.check_lta_available():
                    msg = 'Could not connect to LTA data source'
                    raise InventoryConnectionException(msg)
                results.update(self.check_LTA(lta_ls))
        if lpdaac_ls:
            if not lpdaac.check_lpdaac_available():
                msg = 'Could not connect to LPDAAC data source'
                raise InventoryConnectionException(msg)
            results.update(self.check_LPDAAC(lpdaac_ls))

        not_avail = []
        for key, val in results.items():
            if not val:
                not_avail.append(key)

        if not_avail:
            raise InventoryException(not_avail)

    @staticmethod
    def check_dmid(prod_ls, contactid=None):
        # find all the submitted products that are nlaps and reject them
        not_avail = nlaps.products_are_nlaps(prod_ls)
        if not_avail:
            raise InventoryException(not_avail)
        token = inventory.get_cached_session()
        return inventory.get_cached_verify_scenes(token, contactid, prod_ls)

    @staticmethod
    def check_LPDAAC(prod_ls):
        return lpdaac.verify_products(prod_ls)


class InventoryProvider(InventoryProviderV0):
    pass


class MockInventoryProvider(InventoryInterfaceV0):
    def check(self, order):
        pass
