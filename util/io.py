# Util functions related to general IO
import os
import subprocess
from configparser import ConfigParser
from os import path

from kivy import Logger

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


def run_executable(path_to_file, is_async: bool = False):
    p = subprocess.Popen(path_to_file, cwd=os.getcwd())
    if not is_async:
        return_code = p.wait()
        Logger.info(path_to_file + " exited with code " + return_code)
