import gc
from datetime import datetime

from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

import focus_window
from core.structures import ImageProviderManager
import assets
from main import async_downloader
from uix.widgets import ClickableAsyncImage, FuncImageButton, DataImageButton
from util import utils


class ProviderWindow(Widget):
    provider_manager = None
    provider_buffer = None

    save_path = assets.strings.SAVE_PATH

    def __init__(self, **kwargs):
        super(ProviderWindow, self).__init__(**kwargs)

        self.provider_manager = ImageProviderManager.ProviderManager()

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
                # img = Video(source=entry.image_full)
                pass
            else:
                if entry.image_path and entry.image_path != "":
                    img = ClickableAsyncImage(source=entry.image_path, keep_ratio=True, allow_stretch=True,
                                              extra_headers=self.provider_manager.get_active_provider().get_headers())
                else:
                    img = ClickableAsyncImage(source=entry.image_small, keep_ratio=True, allow_stretch=True,
                                              extra_headers=self.provider_manager.get_active_provider().get_headers())
                img.meta_data = entry
                img.size_hint = (1, 1)
                self.launch_big_viewer
                img.long_press_func = self.save_from_url
                image_pane.add_widget(img)
        return image_pane


def launch_big_viewer(caller: ClickableAsyncImage, provider):
    left_button_size_hint = (1, None)

    outer_holder = None

    def toggle_tag_visibility(inner_caller=None):
        print("toggling")
        if labels.parent:
            labels.parent.remove_widget(labels)
        else:
            outer_holder.add_widget(labels)

    # Build the left menu
    saucenao_search = FuncImageButton(size_hint=left_button_size_hint, source="./assets/images/circle_search.png",
                                      keep_ratio=True, allow_stretch=True, func=utils.choose_saucenao_result)
    saucenao_search.data = caller.meta_data.image_full
    open_in_browser = FuncImageButton(size_hint=left_button_size_hint,
                                      source="./assets/images/circle_open-in-browser.png",
                                      keep_ratio=True, allow_stretch=True)  # handle browser button
    open_in_browser.data = caller.meta_data.image_full

    open_source_in_browser = FuncImageButton(size_hint=left_button_size_hint,
                                             source="./assets/images/circle_source-code.png", keep_ratio=True,
                                             allow_stretch=True)  # handle source button
    open_source_in_browser.data = caller.meta_data.source

    save_to_disk = DataImageButton(size_hint=left_button_size_hint,
                                   source="./assets/images/circle_download.png",
                                   keep_ratio=True, allow_stretch=True)  # handle save-image button
    #save_to_disk.data = caller.meta_data.image_full
    save_to_disk.cg_tap = lambda a, b, c: async_downloader.submit_url(caller.meta_data.image_full)

    expand_tags_button = FuncImageButton(size_hint=left_button_size_hint,
                                         source="./assets/images/circle_expand_tags.png",
                                         keep_ratio=True, allow_stretch=True, func=toggle_tag_visibility)

    debug_timer = datetime.now()
    print("source: " + caller.meta_data.source)
    go_to_src_button = focus_window.build_focus_window_button(caller.meta_data.source)
    print("focus_window.build_focus_window_button done in " + str(datetime.now() - debug_timer))

    left_menu = BoxLayout(orientation='vertical', size_hint=(0.05, 1))  # handle layout
    left_menu.add_widget(saucenao_search)
    left_menu.add_widget(open_in_browser)
    left_menu.add_widget(open_source_in_browser)
    left_menu.add_widget(save_to_disk)
    left_menu.add_widget(expand_tags_button)
    if go_to_src_button:
        left_menu.add_widget(go_to_src_button)

    # Set up big image
    if 'twitter_video' in caller.meta_data.tags:  # Check if the image is a twitter video
        big_image = ClickableAsyncImage(source=caller.meta_data.image_small)
    elif caller.meta_data.image_path and caller.meta_data.image_path != "":  # Check if the image is located on disk
        big_image = ClickableAsyncImage(source=caller.meta_data.image_path)
    else:  # Otherwise, load normally
        big_image = ClickableAsyncImage(source=caller.meta_data.image_full,
                                        extra_headers=self.provider_manager.get_active_provider().get_headers())
    big_image.meta_data = caller.meta_data
    image_container = BoxLayout(size_hint=(1, 1))
    image_container.add_widget(big_image)

    # Build tag container
    labels = GridLayout(cols=3, size_hint=(0.33, 1))
    labels.bind(minimum_height=labels.setter('height'))
    for tag in caller.meta_data.tags:
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
    viewer.title = "Booru Viu"
    viewer.content = outer_holder

    viewer.bind(on_dismiss=self.set_scroller_func)

    viewer.open()

    pass