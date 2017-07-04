"""
"""

import json
from string import Template
from copy import copy
from urllib import urlencode

class Model(object):
    def __init__(self):
        self._original_attrs = None
        self.attrs = {}

    @classmethod
    def query(cls, conn, pattern, method, suffix='', body=None, **kwargs):
        url = Template(pattern).substitute(**kwargs)
        url += suffix

        headers = { 'Content-Accept': 'application/json' }
        if method == 'POST' or method == 'PUT':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            headers["Content-Type"] = "application/json"

        return conn.request(method, url, body, headers)

    def _query(self, method, suffix='', body=None):
        return self.__class__.query(self.conn, self.INSTANCE_PATTERN, method, suffix, body, **self.attrs)

    def _collection_query(self, method, suffix='', body=None):
        return self.__class__.query(self.conn, self.COLLECTION_PATTERN, method, suffix, body, **self.attrs)

    def save(self):
        if self._original_attrs:
            out = {}
            for k in self.attrs:
                if self.attrs[k] != self._original_attrs[k]:
                    out[k] = self.attrs[k]
            params_str = urlencode(out)
            resp, data = self._query('PUT', body=params_str)

        else:
            params_str = urlencode(self.attrs)
            resp, data = self._collection_query('POST', body=params_str)

        self._original_attrs = data
        self.attrs = data


    @classmethod
    def find(cls, conn, **kwargs):
        resp, data = cls.query(conn, cls.INSTANCE_PATTERN, 'GET', **kwargs)
        obj = cls.construct_instance(data)
        obj.conn = conn
        return obj

    @classmethod
    def construct_instance(cls, data):
        obj = cls()
        obj._original_attrs = data
        obj.attrs = copy(data)
        return obj

class Service(Model):
    COLLECTION_PATTERN = '/service'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$id'

    def purge_key(self, key):
        self._query('POST', '/purge/%s' % key)

    def purge_all(self):
        self._query('POST', '/purge_all')

    def details(self):
        resp, data = self._query("GET", "/details")
        return data


class Version(Model):
    COLLECTION_PATTERN = Service.COLLECTION_PATTERN + '/$service_id/version'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$number'

    def check_backends(self):
        resp, data = self._query('GET', '/backend/check_all')
        return data

    def activate(self):
        resp, data = self._query("PUT", "/activate")
        return data


class Domain(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/domain'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

    def check_cname(self):
        resp, data = self._query('GET', '/check')
        return (data[1], data[2])


class Dictionary(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/dictionary'
    INSTANCE_PATTERN = COLLECTION_PATTERN + "/$name"

    @classmethod
    def create(cls, conn, service_id, version, name):
        resp, data = cls.query(
            conn, cls.COLLECTION_PATTERN, "POST",
            service_id=service_id, version=version,
            body=urlencode({"name": name}))
        return data

    @classmethod
    def list(cls, conn, service_id, version):
        resp, data = cls.query(
            conn, cls.COLLECTION_PATTERN, "GET",
            service_id=service_id, version=version)
        return data

    def items(self):
        resp, data = self.__class__.query(
            self.conn,
            Service.COLLECTION_PATTERN + "/$service_id/dictionary/$dictionary_id",
            "GET", "/items",
            None,
            service_id=self.attrs["service_id"],
            dictionary_id=self.attrs["id"])

        return data

    def apply_batch(self, create, update, delete):
        batch = []
        batch.extend(self._create_batch_items("create", create))
        batch.extend(self._create_batch_items("update", update))
        batch.extend(self._create_batch_items("delete", delete))
        body = {"items": batch}

        resp, data = self.__class__.query(
            self.conn,
            Service.COLLECTION_PATTERN + "/$service_id/dictionary/$dictionary_id",
            "PATCH", "/items",
            body=json.dumps(body),
            service_id=self.attrs["service_id"],
            dictionary_id=self.attrs["id"])

        return data

    @staticmethod
    def _create_batch_items(operation, items):
        return [{"op": operation, "item_key": k, "item_value": v} for k, v in items.iteritems()]


class DictionaryItem(Model):
    COLLECTION_PATTERN = Service.COLLECTION_PATTERN + '/$service_id/dictionary/$dictionary_id/items'
    INSTANCE_PATTERN = Service.COLLECTION_PATTERN + '/$service_id/dictionary/$dictionary_id/item/$key'

class Backend(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/backend'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

class Director(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/director'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

class Origin(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/origin'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

class Healthcheck(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/healthcheck'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

class Syslog(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/syslog'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

class User(Model):
    COLLECTION_PATTERN = '/user/$id'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$id'

class Settings(Model):
    INSTANCE_PATTERN = Version.COLLECTION_PATTERN + '/$version/settings'
    COLLECTION_PATTERN = INSTANCE_PATTERN

class Condition(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/condition'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'

class Header(Model):
    COLLECTION_PATTERN = Version.COLLECTION_PATTERN + '/$version/header'
    INSTANCE_PATTERN = COLLECTION_PATTERN + '/$name'
