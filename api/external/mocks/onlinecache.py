import random


def list(self, cmd):
    return {'stdout': ['file1\n', 'file2\n']}


def capacity(self, cmd):
    return {'stdout': ['Filesystem         Size  Used Avail Use% Mounted on\n',
                       'remotehost:/location   10T  9.3T  776G  93% /location\n']}


def delete(self, cmd):
    return {'stdout': ['not checked']}


def mock_capacity():
    return {'capacity': '{}T'.format(random.randint(1, 10)),
             'used': '{}T'.format(random.randint(1, 9)),
             'available': '{}G'.format(random.randint(700, 900)),
             'percent_used': '%'.format(random.randint(1, 100))}


def mock_exists(orderid):
    return True


def mock_delete(orderid):
    return True
