def list(self, cmd):
    return {'stdout': ['file1\n', 'file2\n']}


def capacity(self, cmd):
    return {'stdout': ['Filesystem         Size  Used Avail Use% Mounted on\n',
                       'remotehost:/location   10T  9.3T  776G  93% /location\n']}


def delete(self, cmd):
    return {'stdout': ['not checked']}
