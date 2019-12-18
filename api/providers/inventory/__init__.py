import abc


class InventoryInterfaceV0(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def check(self, order, contactid):
        pass
