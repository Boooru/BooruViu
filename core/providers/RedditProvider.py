import praw
from kivy import Logger
from praw.models import Subreddit

import core.caches
import util.utils
from core.structures.Entry import Entry
from core.structures.ImageProvider import ImageProvider
import assets


class RedditProvider(ImageProvider):

    def __init__(self):
        super().__init__()

        self.internal_index = 0
        self.__reddit_api: praw.Reddit = self.__auth()
        self.__subreddt_generator: Subreddit = None

    def __auth(self):
        if assets.strings.PROVIDER_REDDIT_NAME in core.caches.api_cache and \
                core.caches.api_cache[assets.strings.PROVIDER_REDDIT_NAME]:

            return core.caches.api_cache[assets.strings.PROVIDER_REDDIT_NAME]
        else:
            core.caches.api_cache[assets.strings.PROVIDER_REDDIT_NAME] = \
                praw.Reddit(client_id=core.caches.api_keys[assets.strings.PROVIDER_REDDIT_NAME],
                            user_agent="BooruViu",
                            client_secret=core.caches.api_keys['Reddit Secret'],
                            username=core.caches.api_keys['Reddit Username'],
                            password=core.caches.api_keys['Reddit Password'])

            return core.caches.api_cache[assets.strings.PROVIDER_REDDIT_NAME]

    def __test(self) -> bool:
        askreddit = self.__reddit_api.subreddit('askreddit')
        if askreddit:
            return True
        else:
            return False

    def compose(self) -> str:
        c = ""
        for tag in self.get_tags():
            c = c + tag

        return c

    def search(self, reset_page: bool = True) -> list[Entry]:
        entries = []
        self.internal_index = 0

        if self.get_tags() is None or self.get_tags() == [] or self.get_tags()[0] == "":
            return entries

        if reset_page:
            self.__subreddt_generator = self.__reddit_api.subreddit(self.compose()).hot()

        for submission in self.__subreddt_generator:
            if self.internal_index > self.get_image_limit():
                break

            self.internal_index = self.internal_index + 1

            if submission.selftext != "":
                Logger.info("Skipping self-post: " + submission.url)
                continue

            entries.append(self.make_entry(submission))


        return entries

    def make_entry(self, data: praw.models.Submission) -> Entry:
        e = Entry()
        e.image_full = data.url
        e.image_small = data.url
        e.source = data.permalink
        e.score = data.score
        return e

    def more(self) -> list[Entry]:
        return self.search(reset_page=False)
