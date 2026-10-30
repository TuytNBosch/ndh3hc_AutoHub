import pytest

from autohub.services.WebFlow.dropdown import read_options
from autohub.services.WebFlow.toast import toast_severity


def test_toast_severity_from_the_primeng_class():
    assert toast_severity("ng-trigger p-toast-message-success p-toast-message") == "success"
    assert toast_severity("p-toast-message-error p-toast-message") == "error"
    assert toast_severity("p-toast-message") is None and toast_severity(None) is None


class El:
    def __init__(self, attrs=None, children=None, displayed=True):
        self.attrs, self.children = attrs or {}, children or {}
        self.displayed = displayed

    def get_attribute(self, name):
        return self.attrs.get(name)

    def find_element(self, by, value):
        return self.children[value][0]

    def find_elements(self, by, value):
        return self.children.get(value, [])


class Driver:
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.implicit = [1]

    def implicitly_wait(self, seconds):
        self.implicit.append(seconds)

    def find_element(self, by, value):
        if self.wrapper is None:
            raise LookupError(value)
        return self.wrapper

    def find_elements(self, by, value):
        return [] if self.wrapper is None else [self.wrapper]


def test_every_item_is_read_in_one_query_without_the_old_item_cap():
    items = [El({"aria-label": f"opt{n}"}) for n in range(40)]
    wrapper = El(children={"ul": [El({"id": "x_list"}, {"li[aria-label]": items})]})
    driver = Driver(wrapper)
    options = read_options(driver, "p-dropdown-items-wrapper", 15)
    assert len(options) == 40 and options["opt39"] is items[39]
    assert driver.implicit[-1] == 1 and 0 in driver.implicit  # implicit wait restored afterwards


def test_no_open_list_gives_none():
    assert read_options(Driver(None), "w", 5) is None
