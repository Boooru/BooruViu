from kivy import Logger
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage, Image
from kivy.uix.label import Label

import main
from uix.common_gestures.commongestures import CommonGestures

from core.structures.Entry import Entry


class ClickableAsyncImage(CommonGestures, AsyncImage):
    pass


class MetaDataImage(CommonGestures, AsyncImage):
    def __init__(self, meta_data=Entry(), func=None, **kwargs):
        super().__init__(**kwargs)

        print("Got metadata! " + str(meta_data.image_full))
        self.meta_data = meta_data
        self.func = func

    def cg_tap(self, touch, x, y):
        if self.func:
            self.func(self.meta_data)

    def cg_long_press(self, touch, x, y):
        if self.meta_data and self.meta_data.image_full:
            main.async_downloader.submit_url(self.meta_data.image_full, headers=self.meta_data.headers)
        else:
            Logger.warn("Can't save image with url: " + str(self.meta_data.image_full))


class FuncButton(CommonGestures, Label):
    pass


class FuncImageButton(CommonGestures, Image):
    pass


# A CheckBox that contains an internal text field.
class LabeledCheckBox(CheckBox):
    text: str = ""


# An array of checkboxes. When exclusive is set to true, only one may be selected at a time
class CheckBoxArray(GridLayout):

    def __init__(self, labels: list[str], title: str = None, exclusive: bool = True, on_select=None, **kwargs):

        super().__init__(**kwargs)
        self.cols = 1

        self.__exclusive = exclusive
        self.__label_map = {}

        self.on_select = on_select  # An auxiliary function that can be called whenever any box gets checked
        self.__grid = GridLayout(cols=2, size_hint=(1, 1))  # Main grid layout

        if title:
            self.add_widget(Label(text=title))

        for label in labels:
            self.create_child(label)

        self.add_widget(self.__grid)

    # Add a new checkbox/label pair
    def create_child(self, text: str):
        label = Label(text=text)  # Generate label
        check = LabeledCheckBox()  # Generate check box
        check.text = label.text  # Set the check box's internal text field to the label's text field
        check.bind(active=self.activate)  # Bind the activation function

        # Add box widgets to the outer layout
        self.__grid.add_widget(label)
        self.__grid.add_widget(check)

        self.__label_map[label.text] = check

    # Run each time a box gets checked
    def activate(self, caller: LabeledCheckBox, _):
        if self.__exclusive:
            for child in self.__label_map.values():
                if child is not caller:
                    child.active = False

        if self.on_select is not None and len(self.all_active()) > 0:  # If on_select was set, run it
            print("Running on_select!")
            self.on_select(self.all_active())

    def set_active(self, label_text: str):
        if label_text in self.__label_map:
            self.__label_map[label_text].active = True
        else:
            print("check_array couldn't find " + label_text + " in " + str(self.__label_map))

    # Get the text associated with all checked boxes
    def all_active(self) -> list[str]:
        labels = []
        for child in self.children[0].children:
            if type(child) == LabeledCheckBox and child.active:
                labels.append(child.text)
        print("All active: " + str(labels))
        return labels


class SortDropDown(DropDown):

    def __init__(self, func=None):
        super(SortDropDown, self).__init__()
        mainbutton = Button(text='Select Sort Mode', size_hint=(None, None))
        mainbutton.bind(on_release=self.open)
        self.func = func
        self.bind(on_select=lambda instance, x: func(instance.text))
