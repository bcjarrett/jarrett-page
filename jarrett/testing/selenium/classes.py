import errno
import socket

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.servers.basehttp import ThreadedWSGIServer
from django.test.testcases import LiveServerThread, QuietWSGIRequestHandler


class ConnectionResetErrorSwallowingQuietWSGIRequestHandler(QuietWSGIRequestHandler):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except socket.error as err:
            if err.errno != errno.WSAECONNRESET:
                raise


class ConnectionResetErrorSwallowingLiveServerThread(LiveServerThread):
    def _create_server(self):
        return ThreadedWSGIServer((self.host, self.port), ConnectionResetErrorSwallowingQuietWSGIRequestHandler,
                                  allow_reuse_address=False)


class CustomStaticLiveServerTestCase(StaticLiveServerTestCase):
    server_thread_class = ConnectionResetErrorSwallowingLiveServerThread


class SeleniumBaseTest(CustomStaticLiveServerTestCase):
    web_driver = None
    subdomain = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()
