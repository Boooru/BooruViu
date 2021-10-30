# Util functions related to general IO
import os
from configparser import ConfigParser
from os import path
from assets import strings
from core import caches


def load_api_keys():
    if not path.exists(strings.API_KEY_STORE_PATH):
        print("No keystore found!")
        if not os.path.isdir("./tokens"):
            os.mkdir("./tokens")
        with open(strings.API_KEY_STORE_PATH, 'w') as keystore:
            keystore.write("")
            keystore.close()
    else:
        print("Loading keystore...")
        parser = ConfigParser()
        cfg = parser.read(strings.API_KEY_STORE_PATH)

        keys = {}
        for section in parser.sections():
            keys[section.title()] = parser[section]['key']
        caches.api_keys = keys
