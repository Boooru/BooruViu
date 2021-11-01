# CoreLib imports
import copy
import gc
from datetime import datetime

# 3rd party imports
import requests
from kivy import Logger
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.loader import Loader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.video import Video
from kivy.uix.widget import Widget

import assets.strings
# local imports
import focus_window
import main
from core.structures import ImageProviderManager
from core.structures.Entry import Entry
from uix.effects import ImageOverscroll
from uix.widgets import ClickableAsyncImage, FuncImageButton, CheckBoxArray, MetaDataImage
from util import provider_util, utils
from util.utils import open_link_in_browser


class ProviderWindow(Widget):
    provider_manager = None
    provider_buffer = None

    save_path = assets.strings.SAVE_PATH

    def __init__(self, **kwargs):
        super(ProviderWindow, self).__init__(**kwargs)

        self.provider_manager = ImageProviderManager.ProviderManager()

        self.sorting_mode_setup()

        with self.canvas.before:
            Color(.40, .40, .40, 1)
            self.rect = Rectangle(
                size=Window.size,
                pos=self.pos
            )

    def search(self):
        debug_timer = datetime.now()
        self.set_scroller_func()
        self.ids.image_scroll_view.clear_widgets()
        gc.collect(generation=2)

        self.provider_manager.get_active_provider().clear_tags()
        self.provider_manager.get_active_provider().add_tags_from_string(self.ids.tags.text)

        composition = self.provider_manager.get_active_provider().compose()
        urls = self.provider_manager.get_active_provider().search()

        # Adding GridLayout to ScrollView
        self.ids.image_scroll_view.add_widget(self.generate_image_pane(urls))

    def get_next_page(self, caller=None):
        debug_timer = datetime.now()
        results = self.provider_manager.get_active_provider().more()
        print("get_next_page done with more in " + str(datetime.now() - debug_timer))
        if not results:
            print("No results found!")

        self.generate_image_pane(results, self.ids.image_scroll_view.children[0])

        print("get_next_page done in " + str(datetime.now() - debug_timer))

    def generate_image_pane(self, entries: list, existing_pane=None) -> GridLayout:
        image_pane = GridLayout(cols=3, spacing=0, size_hint=(1, None), pos=(0, 0))
        image_pane.bind(minimum_height=image_pane.setter('height'))
        image_pane.col_default_width = 500
        image_pane.row_default_height = 500

        if existing_pane:
            image_pane = existing_pane
        for entry in entries:
            if entry is None or entry.image_small is None:
                continue
            img = None
            if entry.image_small[-3:] == "mp4":
                print(entry.image_small)
                img = Video(source=entry.image_small)
                pass
            else:
                if entry.image_path and entry.image_path != "":
                    img = MetaDataImage(source=entry.image_path, keep_ratio=True, allow_stretch=True,
                                        extra_headers=self.provider_manager.get_active_provider().get_headers(),
                                        meta_data=entry)
                else:
                    img = MetaDataImage(source=entry.image_small, keep_ratio=True, allow_stretch=True,
                                        extra_headers=self.provider_manager.get_active_provider().get_headers(),
                                        meta_data=entry)
                img.size_hint = (1, 1)
                meta_data = copy.deepcopy(img.meta_data)
                img.func = self.launch_big_viewer
                image_pane.add_widget(img)
        return image_pane

    def set_scroller_func(self, _=None):
        debug_timer = datetime.now()
        if self.ids.image_scroll_view.effect_cls != ImageOverscroll:
            self.ids.image_scroll_view.effect_cls = ImageOverscroll
        self.ids.image_scroll_view.effect_cls.func = self.get_next_page
        print("set_scroller_func done in " + str(datetime.now() - debug_timer))

    def launch_big_viewer(self, meta_data: Entry):
        print("Launching big view")
        print(meta_data.as_dict())
        left_button_size_hint = (1, None)

        outer_holder = None

        def toggle_tag_visibility(inner_caller=None):
            print("toggling")
            if labels.parent:
                labels.parent.remove_widget(labels)
            else:
                outer_holder.add_widget(labels)

        # Build the left menu
        saucenao_search_button = FuncImageButton(size_hint=left_button_size_hint,
                                                 source="./assets/images/circle_search.png",
                                                 keep_ratio=True, allow_stretch=True)
        saucenao_search_button.cg_tap = lambda a, b, c: utils.choose_saucenao_result(meta_data.image_full)

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

        save_to_disk_button.cg_tap = lambda a, b, c: main.async_downloader.submit_url(meta_data.image_full)

        expand_tags_button = FuncImageButton(size_hint=left_button_size_hint,
                                             source="./assets/images/circle_expand_tags.png",
                                             keep_ratio=True, allow_stretch=True)
        expand_tags_button.cg_tap = lambda a, b, c: toggle_tag_visibility()

        go_to_src_button = focus_window.build_focus_window_button(meta_data.source)

        left_menu = BoxLayout(orientation='vertical', size_hint=(0.05, 1))  # handle layout
        left_menu.add_widget(saucenao_search_button)
        left_menu.add_widget(open_in_browser_button)
        left_menu.add_widget(open_source_in_browser_button)
        left_menu.add_widget(save_to_disk_button)
        left_menu.add_widget(expand_tags_button)
        if go_to_src_button:
            left_menu.add_widget(go_to_src_button)

        # Set up big image
        if 'twitter_video' in meta_data.tags:  # Check if the image is a twitter video
            big_image = ClickableAsyncImage(source=meta_data.image_small)
        elif meta_data.image_path and meta_data.image_path != "":  # Check if the image is located on disk
            big_image = ClickableAsyncImage(source=meta_data.image_path)
        else:  # Otherwise, load normally
            big_image = ClickableAsyncImage(source=meta_data.image_full,
                                            extra_headers=self.provider_manager.get_active_provider().get_headers())
        big_image.meta_data = meta_data
        image_container = BoxLayout(size_hint=(1, 1))
        image_container.add_widget(big_image)

        # Build tag container
        labels = GridLayout(cols=3, size_hint=(0.33, 1))
        labels.bind(minimum_height=labels.setter('height'))
        for tag in meta_data.tags:
            button = Button(text=tag)
            button.bind(on_press=self.add_clicked_tag)
            labels.add_widget(button)

        # Set up outer holder
        outer_holder = BoxLayout(size_hint=(1, 1), spacing=10)
        outer_holder.add_widget(left_menu)
        outer_holder.add_widget(image_container)
        # outer_holder.add_widget(labels)

        # Setup popup and launch
        viewer = Popup()
        if meta_data.title and meta_data.title != "":
            viewer.title = meta_data.title + " @ " + str(meta_data.source)
        else:
            viewer.title = str(meta_data.source)
        viewer.content = outer_holder

        viewer.bind(on_dismiss=self.set_scroller_func)

        viewer.open()

        pass

    def add_clicked_tag(self, caller):
        tag = caller.text
        App.get_running_app().root.ids.tags.insert_text(" " + tag)
        self.provider_manager.get_active_provider().add_tag(tag)

    def launch_settings(self):
        viewer = Popup()
        viewer.title = "Settings"
        outer_layout = GridLayout(cols=1)

        provider_check_array = CheckBoxArray(labels=assets.strings.ALL_PROVIDERS,
                                             title="Provider",
                                             on_select=self.set_provider)
        provider_check_array.set_active(provider_util.translate(self.provider_manager.get_active_provider()))

        flows_check_array = CheckBoxArray(labels=main.flow_manager.all_flow_names(),
                                          title="Flows", exclusive=False,
                                          on_select=main.flow_manager.submit_activation_request)
        for flow in main.flow_manager.get_enabled():
            flows_check_array.set_active(flow)

        outer_layout.add_widget(flows_check_array)
        outer_layout.add_widget(provider_check_array)

        viewer.content = outer_layout
        viewer.open()

    def update_save_dir(self, caller):
        self.save_path = caller.text

    def set_provider(self, provs: list[str]):
        self.provider_manager.set_provider(provs[0])

    def open_flows_menu(self, caller=None):
        Logger.warning("Opening flows menu")

    def sorting_mode_setup(self):
        for sort_mode in self.provider_manager.get_active_provider().sorting_modes:
            btn = Button(text=sort_mode, size_hint_y=None, height=44)

            # for each button, attach a callback that will call the select() method
            # on the dropdown. We'll pass the text of the button as the data of the
            # selection.
            btn.bind(on_release=lambda btn: self.ids.sort_by_dropdown.select(btn.text))

            # then add the button inside the dropdown
            self.ids.sort_by_dropdown.add_widget(btn)
            self.ids.sort_by_dropdown.func = self.provider_manager.get_active_provider().sort_by


# Take care of setup before launching the window
class BooruViuApp(App):
    print("Starting app")
    Loader.loading_image = "./assets/images/loading.gif"
    Loader.num_workers = 3
    pass
