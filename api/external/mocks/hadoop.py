def jobs_names_ids(self):
    _d = {'7_28_2016_12_50_7-all-espa_job': 'job_201607260910_1879',
          '7_28_2016_12_46_3-all-espa_job': 'job_201607260910_1875',
          '7_28_2016_12_53_4-all-espa_job': 'job_201607260910_1882',
          '7_28_2016_12_52_5-all-espa_job': 'job_201607260910_1881',
          '7_28_2016_12_39_4-all-espa_job': 'job_201607260910_1874'}
    return _d


def list_jobs(self, cmd):
    return {'stdout': ['job_201607260910_1879', 'job_201607260910_1875']}


def slave_ips(self, cmd):
    return {'stdout': ['localhost\n', 'localhost\n']}

def master_ip(self):
    return '127.0.0.1'
