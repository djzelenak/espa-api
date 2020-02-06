import smtplib
from email.mime.text import MIMEText
import configparser
import os
import subprocess
import datetime
import json

from . import connections
import six


def get_cfg(cfgfile=None):
    """
    Retrieve the configuration information from the .cfgnfo file
    located in the current user's home directory

    :return: dict
    """
    if not cfgfile:
        cfg_path = os.environ['ESPA_CONFIG_PATH']
    else:
        cfg_path = cfgfile

    cfg_info = {}
    config = configparser.ConfigParser()
    config.read(cfg_path)

    for sect in config.sections():
        cfg_info[sect] = {}
        for opt in config.options(sect):
            cfg_info[sect][opt] = config.get(sect, opt)

    return cfg_info


def api_cfg(section='config', cfgfile=None):
    config = get_cfg(cfgfile)[section]
    return config


def send_email(sender, recipient, subject, body):
    """
    Send out an email to give notice of success or failure

    :param sender: who the email is from
    :type sender: string
    :param recipient: list of recipients of the email
    :type recipient: list
    :param subject: subject line of the email
    :type subject: string
    :param body: success or failure message to be passed
    :type body: string
    """
    # This does not need to be anything fancy as it is used internally,
    # as long as we can see if the script succeeded or where it failed
    # at, then we are good to go
    msg = MIMEText(body)
    msg['Subject'] = subject

    # Expecting tuples from the db query
    msg['From'] = ', '.join(sender)
    msg['To'] = ', '.join(recipient)

    smtp = smtplib.SMTP("localhost")
    smtp.sendmail(sender, recipient, msg.as_string())
    smtp.quit()


def backup_cron():
    """
    Make a backup of the current user's crontab
    to /home/~/backups/
    """
    bk_path = os.path.join(os.environ['ESPA_CONFIG_PATH'], 'backups')
    if not os.path.exists(bk_path):
        os.makedirs(bk_path)

    ts = datetime.datetime.now()
    cron_file = ts.strftime('crontab-%m%d%y-%H%M%S')

    with open(os.path.join(bk_path, cron_file), 'w') as f:
        subprocess.call(['crontab', '-l'], stdout=f)


def lowercase_all(indata):
    if hasattr(indata, 'items'):
        ret = {}
        for key, val in indata.items():
            if key.lower() == 'note':
                ret[lowercase_all(key)] = val
            else:
                ret[lowercase_all(key)] = lowercase_all(val)
        return ret

    elif isinstance(indata, six.string_types):
        return indata.lower()

    elif hasattr(indata, '__iter__'):
        ret = []
        for item in indata:
            ret.append(lowercase_all(item))
        return ret

    else:
        return indata


def date_from_doy(year, doy):
    '''Returns a python date object given a year and day of year'''

    d = datetime.datetime(int(year), 1, 1) + datetime.timedelta(int(doy) - 1)

    if int(d.year) != int(year):
        raise Exception("doy [%s] must fall within the specified year [%s]" %
                        (doy, year))
    else:
        return d


def julian_from_date(year, month, day):
    '''Returns a string representation of a julian date for a given year, month, day'''
    dt = datetime.datetime.strptime('.'.join([year, month, day]), '%Y.%m.%d')
    tt = dt.timetuple()
    return str(tt.tm_yday).zfill(3)


def chunkify(lst, n):
    """Divides your list into "n" parts
    :param lst: list of objects to be divided
    :param n: the number of parts to divide list into
    :return: list of lists for pieces of original list
    """
    return [lst[i::n] for i in range(n)]


def julian_date_check(julian_date, restrictions):
    """
    Compare julian dates with a list of formatted restrictions
    to make sure it is a valid date to use

    >>> restrictions = ['< 2015305 | > 2015307', '< 2015365']
    >>> result = julian_date_check(2015306, restrictions)
    >>> assert(result == False)
    >>> result = julian_date_check('2015308', restrictions)
    >>> assert(result == True)

    :param julian_date: integer represention of julian date
    :param restrictions: list/tuple of restrictions
    :return: True if it meets the restriction criteria
    """
    valid_comp = '<>!'

    if not isinstance(julian_date, int):
        try:
            julian_date = int(julian_date)
        except:
            raise ValueError('julian_date variable must be int or be '
                             'transformed to int')

    if not isinstance(restrictions, tuple):
        if isinstance(restrictions, list):
            restrictions = tuple(restrictions)
        elif isinstance(restrictions, six.string_types):
            restrictions = restrictions,

    for r in restrictions:
        r = r.lstrip().rstrip()
        if '|' in r:
            s = False
            for sub in r.split('|'):
                if julian_date_check(julian_date, sub):
                    s = True
                    break

            if not s:
                return False
            else:
                continue

        comp, lim = r.split()

        if comp not in valid_comp:
            raise ValueError('Comparison not implemented: {}'
                             .format(comp))

        if comp == '<':
            if julian_date >= int(lim):
                return False

        elif comp == '>':
            if julian_date <= int(lim):
                return False

        elif comp == '!':
            if julian_date == int(lim):
                return False

    return True


def cond_str(i):
    if not isinstance(i, str):
        return str(i)
    else:
        return i


def conv_dict(i):
    return dict([(cond_str(k), cond_str(v)) for k, v in i.items()])


def json_safe(i):
    i = i.replace("'", '"')
    i = i.replace('None', '"None"')
    i = i.replace(' ', '')
    return i


def jsonify(i):
    return json.loads(json_safe(i))
