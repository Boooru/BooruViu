import os
import re
import sys
import webbrowser
from typing import Optional, Union

from kivy import Logger
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import assets
import core.caches
import util
from uix.layouts import ClickableBoxLayout, DataGridLayout
from uix.widgets import FuncButton


def open_link_in_browser(data):
    from uix.widgets import ClickableAsyncImage

    if type(data) == str:
        webbrowser.open(data, new=0)
    elif isinstance(data, ClickableAsyncImage):
        webbrowser.open(data.meta_data.image_full, new=0)
    elif isinstance(data, ClickableBoxLayout):
        webbrowser.open(data.data['url'])


# Returns the URL of the highest-bitrate MP4 in a twitter post
def best_video_variant(variants: list) -> str:
    best_url = None
    best_bitrate: int = 0

    for var in variants:
        if best_url is None:
            best_url = var['url']
        if 'bitrate' in var:
            if best_bitrate < int(var['bitrate']):
                best_bitrate = int(var['bitrate'])
                best_url = var['url']

    return best_url


def contains_domain(url: str, domain: Union[str, list[str]]) -> Union[bool, str]:
    if type(domain) == str:
        return domain.lower() in re.split("/|\\.", url.lower())
    elif type(domain) == list:
        parts = re.split("/|\\.", url.lower())
        for d in domain:
            if d in parts:
                return d


# Extracts user ID from a url. Supported domains are:
# Twitter
# Pixiv (home page, art page only)
def get_user_from_url(url: str) -> Optional[Union[str, int]]:
    if contains_domain(url, assets.strings.PROVIDER_TWITTER_NAME):
        results = re.findall(assets.strings.TWITTER_USER_REGEX, url)
        return results[0].split("/")[-1]
    if contains_domain(url, assets.strings.PROVIDER_PIXIV_NAME):
        raw_user = re.findall(assets.strings.PIXIV_USER_REGEX, url)
        if raw_user:
            return int(raw_user[0].split("/")[-1])

        raw_artwork = re.findall(assets.strings.PIXIV_ARTWORK_REGEX, url)
        if raw_artwork:
            return get_pixiv_artwork_artist(url)

        raw_illus = re.findall(assets.strings.PIXIV_OLD_ILLUS_REGEX,
                               url)  # Very hacky solution that enables the artist parser to handle outdated illust url
        if raw_illus:
            return get_pixiv_artwork_artist(url.replace("=", "/"))

    return None


# Get the user ID for a given artwork url
def get_pixiv_artwork_artist(url: str) -> Optional[int]:
    artwork_id = int(url.split("/")[-1])  # Split the ID out

    if not artwork_id:
        return None

    util.pixiv_auth.aapi_auth()
    api_response = core.caches.api_cache['pixiv-aapi'].illust_detail(
        artwork_id)  # Ask the API for details about the artwork
    return api_response.illust.user.id  # Return the API's relevant response


def get_saucenao_results(url: str):
    try:
        sys.path.append("venv/Lib/site-packages/")
        from saucenao_api import SauceNao
        from core.caches import api_keys

        sauce = SauceNao(api_keys['saucenao'])
        return sauce.from_url(url)
    except:
        Logger.warn("Couldn't make SauceNao API request!")
        return []


def choose_saucenao_result(url, mode: str = "browser"):
    container = GridLayout(cols=1, size_hint=(1, 1), spacing=3)
    container.bind(minimum_height=container.setter('height'))

    def delegate_press(caller):
        print("Delegating press...")
        if mode == "focus_view":
            pass
        elif mode == "browser":
            open_link_in_browser(caller.data['url'])

    def make_cell(cell_data):
        outer_layout = DataGridLayout(cols=1, size_hint=(1, 0.2))
        thumbnail = AsyncImage(source=cell_data.thumbnail, allow_stretch=True, keep_ratio=True, size_hint=(1, 1))
        title = cell_data.title
        author = cell_data.author
        similarity = cell_data.similarity
        source_info = Label(
            text=str(title) + "\n" + str(author) + "\n" + "Similarity: " + str(similarity) + "%\n")

        inner_layout = GridLayout(rows=1)
        inner_layout.add_widget(thumbnail)
        inner_layout.add_widget(source_info)
        if len(cell_data.urls) > 0:
            url_info = FuncButton(text=cell_data.urls[0])
            url_info.cg_tap = lambda a, b, c: open_link_in_browser(cell_data.urls[0])
            inner_layout.add_widget(url_info)
        outer_layout.add_widget(inner_layout)
        outer_layout.bind(on_press=delegate_press)

        return outer_layout

    for result in get_saucenao_results(url):
        cell = make_cell(result)
        cell.bind(on_press=delegate_press)
        container.add_widget(cell)

    p = Popup(title="Reverse Image Search: Powered by SauceNao")
    p.content = container
    p.open()


def make_temp_dir():
    try:
        os.mkdir("temp")
    except FileExistsError:
        pass

# https://www.redgifs.com/watch/somethinghere
# to
# https://thumbs2.redgifs.com/somethinghere.mp4 if size == None
# or
# https://thumbs2.redgifs.com/somethinghere.mp4-mobile if size == "mobile"
def transform_redgif(url:str, size="") -> str:
    if contains_domain(url, "redgifs") or contains_domain(url, 'gyfcat'):
        from bs4 import BeautifulSoup
        import urllib.request

        # Build the request, then get the result
        req = urllib.request.Request(url)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/87.0.4280.88 Safari/537.36')
        content = urllib.request.urlopen(req)
        read_content = content.read()

        # Parse the data from the result
        soup = BeautifulSoup(read_content, 'html.parser')
        v_element = soup.find_all("meta", {"property": "og:video"})

        return v_element[0].get('content')

