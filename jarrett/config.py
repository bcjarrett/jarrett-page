import json
import os

from django.core.exceptions import ImproperlyConfigured


class Config:

    def __init__(self):
        try:
            with open('secrets.json') as env:
                self.json_secrets = json.loads(env.read())
                return
        except (IOError, json.decoder.JSONDecodeError):
            self.json_secrets = None
        return

    def __getitem__(self, item):
        try:
            if self.json_secrets:
                return self.json_secrets[item]
            else:
                return os.environ[item]
        except KeyError:
            raise ImproperlyConfigured(f'{item} is not in the local environment or your secrets.json file')

    def get(self, item, default):
        try:
            return self.__getitem__(item)
        except (KeyError, ImproperlyConfigured):
            return default
