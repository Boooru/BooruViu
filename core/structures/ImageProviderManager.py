import os
from configparser import ConfigParser

from kivy import Config

from core.structures import ImageProvider
import assets.strings
from util import provider_util


class ProviderManager:
    DEFAULT_PROVIDER = assets.strings.PROVIDER_GELBOORU_NAME

    def __init__(self):
        self.__provider = None
        self.__user_rules = {}

        for name in assets.strings.ALL_PROVIDERS:
            self.__user_rules[name] = {"tags": "",
                                       "blacklist": "",
                                       "limit": None,
                                       "always_safe": None
                                       }

        if os.path.exists(assets.strings.CONFIG_FILE_NAME):
            parser = ConfigParser()
            parser.read(assets.strings.CONFIG_FILE_NAME)

            for section in parser.sections():
                if section.title() in assets.strings.ALL_PROVIDERS:
                    for value in parser[section.title()].keys():
                        self.__user_rules[section.title()][value] = parser[section.title()][value]
                elif section.title() == "Main":
                    if "default_provider" in parser[section.title()].keys():
                        self.DEFAULT_PROVIDER = parser[section.title()]["default_provider"]
        else:
            cf = open(assets.strings.CONFIG_FILE_NAME, 'x')
            cf.close()

        self.set_provider(self.DEFAULT_PROVIDER)

    def clear(self) -> None:
        self.__provider = None

    def get_active_provider(self) -> ImageProvider:
        return self.__provider

    def set_provider(self, provider_name: str):
        self.__provider = (provider_util.translate(provider_name))()
        Config.set('network', 'referer', "")

        if "tags" in self.__user_rules[provider_name] and self.__user_rules[provider_name]["tags"]:
            self.__provider.add_tags_from_string(tags=self.__user_rules[provider_name]["tags"])

        if "blacklist" in self.__user_rules[provider_name] and self.__user_rules[provider_name]["blacklist"]:
            self.__provider.blacklist_tags_from_string(tags=self.__user_rules[provider_name]["blacklist"])

        if "limit" in self.__user_rules[provider_name] and self.__user_rules[provider_name]["limit"]:
            self.__provider.set_limit(limit=int(self.__user_rules[provider_name]["limit"]))
        else:
            self.__provider.set_limit(10)

        if "always_safe" in self.__user_rules[provider_name] and self.__user_rules[provider_name]["always_safe"]:
            self.__provider.set_always_safe(bool(self.__user_rules[provider_name]['always_safe']))
