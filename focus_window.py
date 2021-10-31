import gc
from datetime import datetime
from typing import Optional

import requests
from kivy.app import App
from kivy.core.window import Window

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import assets
import main
from util import provider_util
from util.utils import open_link_in_browser
from core.structures.ImageProvider import ImageProvider
from uix.effects import ImageOverscroll
from uix.widgets import ClickableAsyncImage, FuncImageButton, MetaDataImage
from util.utils import get_user_from_url, contains_domain


class FocusWindow(Widget):
    save_path = assets.strings.SAVE_PATH
    headers = None
    config = None
    provider: ImageProvider = None

    def __init__(self, provider=None, config=None, **kwargs):
        super(FocusWindow, self).__init__(**kwargs)
        self.config = {}

        if provider:
            self.provider = provider
            self.provider.clear_tags()
            self.provider.clear_blacklist()

        if config:
            self.config = config

        if 'tags' in self.config:
            print("Tags from provider: " + str(config['tags']))
            self.provider.add_tags_from_string(str(self.config['tags']))
            print("Tags after set: " + str(self.provider.get_tags()))
        if 'blacklist' in self.config:
            self.provider.blacklist_tags_from_string(self.config['blacklist'])
        if 'limit' in self.config:
            self.provider.set_limit(self.config['limit'])

        self.C_L = GridLayout(cols=3, spacing=0, size_hint=(1, None), pos=(0, 0))
        self.C_L.bind(minimum_height=self.C_L.setter('height'))
        self.C_L.col_default_width = 500
        self.C_L.row_default_height = 500

        self.scroller = ScrollView()
        self.scroller.do_scroll_y = True
        self.scroller.do_scroll_x = False
        self.scroller.always_overscroll = True

        outer_layout = BoxLayout(size=Window.size)
        outer_layout.orientation = "vertical"
        outer_layout.add_widget(self.scroller)
        self.add_widget(outer_layout)
        if self.provider:
            self.headers = self.provider.get_headers()
            self.search()

    def __del__(self):
        gc.collect(generation=2)

    def search(self):
        self.scroller.effect_cls = ImageOverscroll
        self.scroller.effect_cls.func = self.get_next_page

        composition = self.provider.compose()
        urls = self.provider.search()

        print("Composition: " + str(composition))

        # Adding All images to GridLayout
        print("Adding from search...")
        print("Current headers: ")
        print(self.headers)
        for entry in urls:
            if entry is None or entry.image_small is None:
                print("Couldn't process entry!")
                continue
            img = None
            if entry.image_small[-3:] == "mp4":
                # img = Video(source=entry.image_full)
                pass
            else:
                if entry.image_path and entry.image_path != "":
                    img = MetaDataImage(source=entry.image_path, keep_ratio=True, allow_stretch=True,
                                        extra_headers=self.headers)
                else:
                    img = MetaDataImage(source=entry.image_small, keep_ratio=True, allow_stretch=True,
                                        extra_headers=self.headers)
                img.meta_data = entry
                img.size_hint = (1, 1)
                img.func = self.launch_big_viewer
                self.C_L.add_widget(img)

        # Adding GridLayout to ScrollView
        self.scroller.add_widget(self.C_L)

    def launch_big_viewer(self, meta_data):
        left_button_size_hint = (1, None)
        # Build the left menu
        open_in_browser_button = FuncImageButton(size_hint=left_button_size_hint,
                                                 source="./assets/images/circle_open-in-browser.png",
                                                 keep_ratio=True, allow_stretch=True)  # handle browser button
        open_in_browser_button.cg_tap = lambda a, b, c: open_link_in_browser(meta_data.image_full)

        open_source_in_browser_button = FuncImageButton(size_hint=left_button_size_hint,
                                                        source="./assets/images/circle_source-code.png",
                                                        keep_ratio=True,
                                                        allow_stretch=True)  # handle source button
        open_source_in_browser_button.cg_tap = lambda a, b, c: open_link_in_browser(meta_data.source)

        save_to_disk_button = FuncImageButton(size_hint=left_button_size_hint,
                                              source="./assets/images/circle_download.png",
                                              keep_ratio=True, allow_stretch=True)  # handle save-image button

        save_to_disk_button.cg_tap = lambda a, b, c: \
            main.async_downloader.submit_url(meta_data.image_full,
                                             headers=self.provider.get_headers())

        left_menu = BoxLayout(orientation='vertical', size_hint=(0.05, 1))  # handle layout
        left_menu.add_widget(open_in_browser_button)
        left_menu.add_widget(open_source_in_browser_button)
        left_menu.add_widget(save_to_disk_button)

        # Set up big image
        if 'twitter_video' in meta_data.tags:
            big_image = MetaDataImage(source=meta_data.image_small)
        elif meta_data.image_path and meta_data.image_path != "":
            big_image = MetaDataImage(source=meta_data.image_path)
        else:
            big_image = MetaDataImage(source=meta_data.image_full,
                                      extra_headers=self.headers)

        # big_image.bind(on_press=self.save_from_url)
        big_image.meta_data = meta_data
        image_container = BoxLayout(size_hint=(0.66, 1))
        image_container.add_widget(big_image)

        # Build tag container
        labels = GridLayout(cols=3)
        labels.bind(minimum_height=labels.setter('height'))
        for tag in meta_data.tags:
            button = Button(text=tag)
            labels.add_widget(button)

        # Set up outer holder
        outer_holder = BoxLayout(size_hint=(1, 1), spacing=10)
        outer_holder.add_widget(left_menu)
        outer_holder.add_widget(image_container)
        outer_holder.add_widget(labels)

        # Setup popup and launch
        viewer = Popup()
        viewer.title = "BooruViu"
        viewer.content = outer_holder
        viewer.open()

        pass

    def get_next_page(self, caller=None):
        results = self.provider.more()
        if not results:
            print("No results found!")
        for entry in results:
            if entry is None or entry.image_full is None:
                continue
            img = None
            if entry.image_full[-3:] == "mp4":
                # img = Video(source=entry.image_full)
                pass
            else:
                img = MetaDataImage(source=entry.image_full, keep_ratio=True, allow_stretch=True,
                                          extra_headers=self.headers)
                img.meta_data = entry
                img.func = self.launch_big_viewer
                img.size_hint = (1, 1)
                self.C_L.add_widget(img)


def build_focus_window_button(url: str) -> Optional[FuncImageButton]:
    button = None
    provider_name = None
    config = None

    if contains_domain(url, assets.strings.PROVIDER_TWITTER_NAME):
        button = FuncImageButton(size_hint=(1, None), keep_ratio=True, allow_stretch=True)
        button.source = "./assets/images/circle_twitter.png"
        config = {"tags": get_user_from_url(url)}
        provider_name = assets.strings.PROVIDER_TWITTER_NAME

    elif contains_domain(url, assets.strings.PROVIDER_PIXIV_NAME):
        button = FuncImageButton(size_hint=(1, None), keep_ratio=True, allow_stretch=True)
        config = {}
        button.source = "./assets/images/circle_pixiv.png"
        provider_name = assets.strings.PROVIDER_PIXIV_NAME

    if button:
        button.cg_tap = lambda a, b, c: launch_focus_window(url, provider_name, config)
        return button


def launch_focus_window(url: str, provider_name: str, config: dict = None, ):
    print("Launching focussed window:")

    user = get_user_from_url(url)
    if user:
        config['tags'] = str(user)
    else:
        open_link_in_browser(url)
        return

    print("config: " + str(config))

    p = Popup()
    fw = FocusWindow(config=config, provider=provider_util.translate(provider_name)())
    p.content = fw
    p.title = "Focused View"
    p.open()
