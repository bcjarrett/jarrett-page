from django.conf import settings
from selenium.webdriver import Chrome, Edge, Firefox

IMPLICIT_WAIT_TIME = settings.SELENIUM_IMPLICIT_WAIT_TIME


class ChromeMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.web_driver = Chrome()
        cls.web_driver.maximize_window()
        cls.web_driver.implicitly_wait(IMPLICIT_WAIT_TIME)


class EdgeMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.web_driver = Edge()
        cls.web_driver.maximize_window()
        cls.web_driver.implicitly_wait(IMPLICIT_WAIT_TIME)


class FirefoxMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.web_driver = Firefox()
        cls.web_driver.maximize_window()
        cls.web_driver.implicitly_wait(IMPLICIT_WAIT_TIME)
