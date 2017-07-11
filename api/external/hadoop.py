from api.domain.user import User
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.providers.caching.caching_provider import CachingProvider
from api.util.sshcmd import RemoteHost
import socket
cache = CachingProvider()
config = ConfigurationProvider()


class HadoopHandler(object):

    def list_jobs(self):
        return self._remote_cmd('yarn application -appStates RUNNING -list')

    def kill_job(self, jobid):
        return self._remote_cmd('hadoop job -kill {}'.format(jobid))

    def kill_user_jobs(self, username):
        _response = dict()
        try:
            for job_name in User.by_username(username).active_hadoop_job_names():
                _response[job_name] = self.kill_job(self.job_names_ids()[job_name])
        except AttributeError, e:
            if "object has no attribute 'active_hadoop_job_names'" in e.message:
                _response['msg'] = 'user not found'
            else:
                raise e

        return _response

    def job_names_ids(self):
        cache_key = "jobs_names_cache"
        resp = cache.get(cache_key)

        if not resp:
            _stdout = self.list_jobs()['stdout']
            _id_name_list = [str(i).rstrip('\n') for i in _stdout]
            resp = {}
            for ids in _id_name_list:
                ids_list = ids.split(' ')
                resp[ids_list[1]] = ids_list[0]
            cache.set(cache_key, resp, 180)

        return resp

    def slave_ips(self):
        _stdout = self._remote_cmd("cat ~/bin/hadoop/etc/hadoop/slaves")['stdout']
        _host_list = [str(i).rstrip('\n') for i in _stdout]
        return [socket.gethostbyname(i) for i in _host_list]

    def master_ip(self):
        master_host = config.get('hadoop.master')
        return socket.gethostbyname(master_host)

    def _remote_cmd(self, cmd):
        params = ('hadoop.master',
                  'landsatds.username',
                  'landsatds.password')

        remote = RemoteHost(*config.get(params))
        resp = remote.execute(cmd)
        return resp
