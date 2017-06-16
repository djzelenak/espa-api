import abc


class InventoryInterfaceV0(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def check(self, order, contactid):
        pass
