"""Builds the Edge driver service: a given msedgedriver, or one downloaded through the Bosch proxy."""
from __future__ import annotations

import requests
from requests import Response
from selenium.webdriver.edge.service import Service
from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.http import HttpClient
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from . import Constants


class CustomHttpClient(HttpClient):
    """Downloads the driver through the proxy in ``Constants.WEBDRIVER_DOWNLOAD_PROXY``."""

    def get(self, url, params=None, **kwargs) -> Response:
        proxy = Constants.WEBDRIVER_DOWNLOAD_PROXY
        return requests.get(url, params, proxies={"http": proxy, "https": proxy}, **kwargs)


def edge_service(driver_path: str = "") -> Service:
    if driver_path:
        return Service(driver_path)
    download_manager = WDMDownloadManager(CustomHttpClient())
    return Service(EdgeChromiumDriverManager(download_manager=download_manager).install())
