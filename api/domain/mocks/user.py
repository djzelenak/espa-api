import os
from api.domain.user import User
from api.util.dbconnect import db_instance


class MockUserException(Exception):
    pass


class MockUser(object):
    """ class for mocking the User class in unit tests """

    def __init__(self):
        try:
            mode = os.environ['espa_api_testing']
            if mode != 'True':
                raise MockUserException("MockUser objects only allowed while testing")
        except Exception:
            raise MockUserException("MockUser objects only allowed while testing")

    def __repr__(self):
        return "MockUser: {0}".format(self.__dict__)

    def add_testing_user(self):
        """ add user record to test schemas auth_user table """
        user = User('bilbo_baggins', 'bilbo@usgs.gov', 'bilbo', 'baggins', '123456')
        return user.id

    def cleanup(self):
        sql = "DELETE from auth_user where id > 0;"
        with db_instance() as db:
            db.execute(sql)
            db.commit()

    @classmethod
    def get(cls, *args):
        user = User.where({'username': 'bilbo_baggins'})[0]
        return user.username, user.email, user.first_name, user.last_name, user.contactid
