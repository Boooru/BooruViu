import os

from kivy import Config, platform
from kivy.core.window import Window

import ui
import util.io as io

from flow.preprocessing.download import AsyncDownloader
from flow.flow_manager import FlowManager

# Globals
async_downloader = AsyncDownloader()
flow_manager = FlowManager()


def root():
    Config.set('graphics', 'resizable', True)
    Window.size = (1920, 1080)
    ui.BooruViuApp().run()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        if platform == 'win':
            # Dispose of that nasty red dot on Windows
            Config.set('input', 'mouse', 'mouse, disable_multitouch')

        io.load_api_keys()
        root()

    except:
        input("Press any key to exit")
        raise

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
