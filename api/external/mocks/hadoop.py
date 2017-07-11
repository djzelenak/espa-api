def jobs_names_ids(self):
    _d = {'7_28_2016_12_50_7-all-espa_job': 'job_201607260910_1879',
          '7_28_2016_12_46_3-all-espa_job': 'job_201607260910_1875',
          '7_28_2016_12_53_4-all-espa_job': 'job_201607260910_1882',
          '7_28_2016_12_52_5-all-espa_job': 'job_201607260910_1881',
          '7_28_2016_12_39_4-all-espa_job': 'job_201607260910_1874'}
    return _d


def list_jobs(self, cmd):
    return {'stdout': ['Total number of applications (application-types: [] and states: [RUNNING]):1\n',
                       '                Application-Id      Application-Name        Application-Type          User           Queue                   State      Final-State              Progress                        Tracking-URL\n',
                       'application_1499729760759_0002  7_10_2017_17_11_2-all-espa_job             MAPREDUCE       SOMEUSER         default                 RUNNING              UNDEFINED                   5% http://HOSTNAME:00000\n']}


def slave_ips(self, cmd):
    return {'stdout': ['localhost\n', 'localhost\n']}

def master_ip(self):
    return '127.0.0.1'
