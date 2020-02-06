import sys
import time
import traceback
import datetime

from passlib.hash import pbkdf2_sha256
from validate_email import validate_email

from api.domain import format_sql_params
from api.external.ers import ERSApi
from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.system.logger import ilogger as logger
from api.util.dbconnect import db_instance, DBConnectException
import six

ers = ERSApi()


class UserException(Exception):
    pass


class User(object):

    base_sql = "SELECT username, email, first_name, last_name, contactid "\
                "FROM auth_user WHERE "

    def __init__(self, username, email, first_name, last_name, contactid):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.contactid = contactid
        self.id = self.find_or_create_user()

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected a string')
        self._username = value

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected a string')
        self._first_name = value

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected a string')
        self._last_name = value

    @property
    def contactid(self):
        return self._contactid

    @contactid.setter
    def contactid(self, value):
        if not isinstance(value, str):
            raise TypeError('Expected a string')
        self._contactid = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not validate_email(value):
            raise Exception('user email value invalid')
        self._email = value.strip()

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if not isinstance(value, int):
            raise TypeError('Expected an integer')
        self._id = value

    def __repr__(self):
        return self.as_dict()

    @classmethod
    def get(cls, username, password):
        if username == 'espa_admin':
            cp = ConfigurationProvider()
            if pbkdf2_sha256.verify(password, cp.espa256):
                return username, cp.get('apiemailreceive'), 'espa', 'admin', ''
            else:
                msg = "ERR validating espa_admin, invalid password "
                logger.critical(msg)
                raise UserException(msg)
        else:
            eu = ers.get_user_info(username, password)
            return eu['username'], eu['email'], eu['firstName'], eu['lastName'], eu['contact_id']

    def find_or_create_user(self):
        """ check if user exists in our DB, if not create them
            returns what should be assigned to self.id
        """
        (username, email, first_name, last_name, contactid) = (
            self.username, self.email, self.first_name, self.last_name, self.contactid)
        user_id = None
        nownow = time.strftime('%Y-%m-%d %H:%M:%S')
        insert_stmt = "insert into auth_user (username, " \
                      "email, first_name, last_name, password, " \
                      "is_staff, is_active, is_superuser, " \
                      "last_login, date_joined, contactid) values " \
                      "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) " \
                      "on conflict (username) " \
                      "do update set (email, contactid, last_login) = (%s, %s, %s) " \
                      "where auth_user.username = %s" \
                      "returning id"
        arg_tup = (username, email, first_name, last_name,
                   'pass', 'f', 't', 'f', nownow, nownow, contactid,
                   email, contactid, nownow, username)

        with db_instance() as db:
            try:
                db.execute(insert_stmt, arg_tup)
                db.commit()
                user_id = db.fetcharr[0]['id']
            except:
                exc_type, exc_val, exc_trace = sys.exc_info()
                logger.critical("ERR user find_or_create args {0} {1} " \
                                "{2} {3}\n trace: {4}".format(username, email, first_name,
                                                              last_name, traceback.format_exc()))
                six.reraise(exc_type, exc_val, exc_trace)

        return user_id

    @classmethod
    def where(cls, params):
        """
        Query for particular users

        :param params: dictionary of column: value parameters
        :return: list of matching User objects
        """
        if not isinstance(params, dict):
            raise UserException('Where arguments must be passed as a dictionary')

        sql, values = format_sql_params(cls.base_sql, params)

        ret = []
        log_sql = ''
        try:
            with db_instance() as db:
                log_sql = db.cursor.mogrify(sql, values)
                logger.info('user.py where sql: {}'.format(log_sql))
                db.select(sql, values)
                for i in db:
                    obj = User(i["username"], i["email"], i["first_name"],
                               i["last_name"], i["contactid"])
                    ret.append(obj)
        except DBConnectException as e:
                num, message = e.args
                logger.critical('Error querying for users: {}\n'
                                'sql: {}'.format(message, log_sql))
                raise UserException(e)
        return ret

    @classmethod
    def by_contactid(cls, contactid):
        try:
            return cls.where({'contactid': contactid})[0]
        except IndexError:
            return None

    @classmethod
    def by_username(cls, username):
        try:
            return cls.where({'username': username})[0]
        except IndexError:
            return None

    @classmethod
    def find(cls, ids):
        sql = '{} id IN %s;'.format(cls.base_sql)
        resp = list()
        if not isinstance(ids, list) and not isinstance(ids, int):
            raise UserException("a list of integers, or a single integer, "
                                 "are the only valid arguments for User.find()")

        if isinstance(ids, list):
            _single = False
            for item in ids:
                if not isinstance(item, int):
                    raise UserException("list members must be of type int for "
                                         "User.find(): {0} is not an int".format(item))
        else:
            _single = True
            ids = [ids]

        with db_instance() as db:
            db.select(sql, [tuple(ids)])

        if db:
            for i in db:
                obj = User(i["username"], i["email"], i["first_name"],
                               i["last_name"], i["contactid"])
                resp.append(obj)

        if _single:
            return resp[0]
        else:
            return resp

    def update(self, att, val):
        self.__setattr__(att, val)
        if isinstance(val, str) or isinstance(val, datetime.datetime):
            val = "\'{0}\'".format(val)
        sql = "update auth_user set {0} = {1} where id = {2};".format(att, val, self.id)
        with db_instance() as db:
            db.execute(sql)
            db.commit()
        return True

    def roles(self):
        result = None
        with db_instance() as db:
            db.select("select is_staff, is_active, is_superuser from auth_user where id = %s;" % self.id)
        try:
            result = db[0]
        except:
            exc_type, exc_val, exc_trace = sys.exc_info()
            logger.critical("ERR retrieving roles for user. msg{0} trace{1}".format(exc_val, traceback.format_exc()))
            six.reraise(exc_type, exc_val, exc_trace)

        return result

    def is_staff(self):
        return self.roles()['is_staff']

    def active(self):
        # is_active is already a method of UserMixin
        return self.roles()['is_active']

    def is_superuser(self):
        return self.roles()['is_superuser']

    def role_list(self):
        out_list = []
        if self.is_staff():
            out_list.append('staff')
        if self.is_superuser():
            out_list.append('super')
        if self.active():
            out_list.append('active')

        return out_list

    def as_dict(self):
        return {"email": self.email,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "username": self.username,
                "roles": self.role_list()}


