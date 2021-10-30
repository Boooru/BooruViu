# This class contains the BooruProvider base class and all of its direct children.
# Note that providers that significantly modify BooruProvider's functionality, or inherit deeply from it, may
# be located in a different class.

from core.structures.Entry import Entry
from core.structures.ImageProvider import ImageProvider


class BooruProvider(ImageProvider):
    provider_url = ""

    def __init__(self):
        super().__init__()
        self.user_id = ""
        self.user_api = ""

    def compose(self) -> str:
        req = self.provider_url

        # handle tags
        req = req + "&tags="
        for tag in self.get_tags():
            req = req + "+" + tag

        # insert blacklisted tags
        for tag in self.get_blacklisted_tags():
            req = req + "+-" + tag

        # handle safety
        if self.is_always_safe():
            req = req + "+rating:safe"

        # handle limit
        if int(self.get_image_limit()) > 0:
            req = req + "&limit=" + str(self.get_image_limit())

        if self.get_score_limit() >= 0:
            req = req + "&score:>=" + str(self.get_score_limit())

        if self.sort_by is not None:
            if self.sort_by == self.SCORE_SORT:
                req = req + "&sort:score:desc"
            elif self.sort_by == self.RANDOM_SORT:
                req = req + "&sort:random"

        req = req + "&pid=" + str(self.page_number)

        req = req + "&json=1"

        return req

    def make_entry(self, data: dict) -> Entry:
        try:
            en = Entry()
            en.image_full = data["file_url"].replace("\\", "")
            en.image_small = en.image_full
            en.source = data["source"].replace("\\", "")
            en.tags = data["tags"].split(" ")
            en.headers = self.get_headers()
            return en
        except:
            print("Failed to make entry: ")
            print(data)


class GelbooruProvider(BooruProvider):

    def __init__(self):
        super().__init__()
        self.provider_url = "http://gelbooru.com/index.php?page=dapi&s=post&q=index"


class SafebooruProvider(BooruProvider):

    def __init__(self):
        super().__init__()
        self.provider_url = "http://safebooru.org/index.php?page=dapi&s=post&q=index"

    def make_entry(self, data: dict) -> Entry:
        try:
            en = Entry()
            image_url = "https://safebooru.org//images/{directory}/{image}".format(directory=data['directory'],
                                                                                   image=data['image'])
            en.image_full = image_url
            en.image_small = en.image_full
            en.source = ""
            en.tags = data["tags"].split(" ")
            en.headers = self.get_headers()
            return en
        except:
            print("Failed to make entry: ")
            print(data)


class Rule34Provider(BooruProvider):

    def __init__(self):
        super().__init__()
        self.provider_url = "https://rule34.xxx/index.php?page=dapi&s=post&q=index"

    def make_entry(self, data: dict) -> Entry:
        en = Entry()
        en.image_full = data["file_url"].replace("\\", "")
        en.image_small = data["sample_url"].replace("\\", "")
        en.source = None
        en.tags = data["tags"].split(" ")
        en.headers = self.get_headers()
        return en
