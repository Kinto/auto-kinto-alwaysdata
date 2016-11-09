# -*- coding: utf-8 -*-
import hashlib
import requests
import ftplib
from paramiko.client import SSHClient, AutoAddPolicy
from six import StringIO

# CONFIGURATION
LOGIN = "EMAIL_ADDRESS"
PASSWORD = "AD_PASSWORD"
ID_ALWAYSDATA = "AD_USERNAME"

credentials = (LOGIN, PASSWORD)

# CALCULATE VALUES
settings = {
    'id_alwaysdata': ID_ALWAYSDATA,
    'login': LOGIN,
    'password': PASSWORD,
    'postgresql_host': "postgresql-%s.alwaysdata.net" % ID_ALWAYSDATA,
    'ssh_host': "ssh-%s.alwaysdata.net" % ID_ALWAYSDATA,
    'ftp_host': "ftp-%s.alwaysdata.net" % ID_ALWAYSDATA,
    'prefixed_username': "%s_kinto" % ID_ALWAYSDATA,
    'hmac_secret': hashlib.sha256(':'.join(credentials)).hexdigest()
}

# Create database
response = requests.post("http://api.alwaysdata.com/v1/database/", json={
    "name": settings['prefixed_username'],
    "type": "POSTGRESQL",
    "permissions": {ID_ALWAYSDATA: "FULL"}
}, auth=credentials)
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as error:
    # The database may already exist.
    if error.response.status_code != 400:
        raise
    else:
        print("Database `%s` already exists." % "%s_kinto" % ID_ALWAYSDATA)
else:
        print("Database `%s` created." % "%s_kinto" % ID_ALWAYSDATA)

# Build configuration
config = """
[app:main]
use = egg:kinto

pyramid.debug_notfound = false

kinto.http_scheme = https
kinto.http_host = https://%(id_alwaysdata)s.alwaysdata.net/

kinto.project_name = kinto
kinto.project_docs = https://kinto.readthedocs.io/

#
# Backends.
#
kinto.cache_backend = kinto.core.cache.postgresql
kinto.cache_url = postgres://%(id_alwaysdata)s:%(password)s@%(postgresql_host)s/%(prefixed_username)s

kinto.storage_backend = kinto.core.storage.postgresql
kinto.storage_url = postgres://%(id_alwaysdata)s:%(password)s@%(postgresql_host)s/%(prefixed_username)s

kinto.permission_backend = kinto.core.permission.postgresql
kinto.permission_url = postgres://%(id_alwaysdata)s:%(password)s@%(postgresql_host)s/%(prefixed_username)s

# kinto.backoff = 10
kinto.batch_max_requests = 25
# kinto.retry_after_seconds = 30
# kinto.eos =

#
# Auth configuration.
#
kinto.userid_hmac_secret = %(hmac_secret)s
multiauth.policies = basicauth

[loggers]
keys = root, kinto

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_kinto]
level = DEBUG
handlers =
qualname = kinto

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %%(asctime)s %%(levelname)-5.5s [%%(name)s][%%(threadName)s] %%(message)s

# End logging configuration
""" % settings

# Create ssh user
response = requests.post("http://api.alwaysdata.com/v1/ssh/", json={
    "name": settings['prefixed_username'],
    "password": PASSWORD
}, auth=credentials)
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as error:
    # The database may already exist.
    if error.response.status_code != 400:
        raise
    else:
        print("SSH User `%s` already exists." % "%s_kinto" % ID_ALWAYSDATA)
else:
        print("SSH User `%s` created." % "%s_kinto" % ID_ALWAYSDATA)

# Copy the config
ftp = ftplib.FTP(settings['ftp_host'], ID_ALWAYSDATA, PASSWORD)
try:
    ftp.mkd(".local")
except ftplib.error_perm:
    pass
try:
    ftp.mkd("kinto")
except ftplib.error_perm:
    pass
try:
    ftp.storbinary("STOR kinto/kinto.ini", StringIO(config))
except ftplib.error_perm:
    print("A kinto config already exist.")
else:
    print("A kinto config has been uploaded.")
ftp.close()

# Install kinto[postgresql]

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(settings['ssh_host'], username=settings['prefixed_username'],
            password=PASSWORD, look_for_keys=False)
stdin, stdout, stderr = ssh.exec_command('PYTHONPATH=~/.local/ easy_install-2.6 --install-dir=~/.local -U pip')
print(stdout.read(), stderr.read())
stdin, stdout, stderr = ssh.exec_command('PYTHONPATH=~/.local/ ~/.local/pip install --user --no-binary --upgrade setuptools virtualenv virtualenvwrapper')
print(stdout.read(), stderr.read())
stdin, stdout, stderr = ssh.exec_command('~/.local/bin/virtualenv kinto/venv/ --python=python2.7')
print(stdout.read(), stderr.read())
stdin, stdout, stderr = ssh.exec_command('kinto/venv/bin/pip install kinto[postgresql]')
print(stdout.read(), stderr.read())
ssh.close()
