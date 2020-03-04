import os

DEBUG = True

SECRET_KEY = os.urandom(24)

DIALECT = 'mysql'  # type of database
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = ''   # password for your own database
HOST = 'localhost'  # server
PORT = '3306'
DATABASE = 'language'  # name of database

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False
