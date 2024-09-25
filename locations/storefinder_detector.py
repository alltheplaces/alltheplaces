import re
from copy import deepcopy
from typing import Any, Iterable
from urllib.parse import parse_qsl

import jq
from playwright.async_api import Frame
from playwright.async_api import Request as PlaywrightRequest
from scrapy import Selector, Spider
from scrapy.http import Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule, DetectionResponseRule
from locations.items import GeneratedSpider
from locations.name_suggestion_index import NSI
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider
from locations.storefinders.aheadworks import AheadworksSpider
from locations.storefinders.algolia import AlgoliaSpider
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider
from locations.storefinders.amrest_eu import AmrestEUSpider
from locations.storefinders.closeby import ClosebySpider
from locations.storefinders.easy_locator import EasyLocatorSpider
from locations.storefinders.freshop import FreshopSpider
from locations.storefinders.geo_me import GeoMeSpider
from locations.storefinders.kibo import KiboSpider
from locations.storefinders.lighthouse import LighthouseSpider
from locations.storefinders.limesharp_store_locator import LimesharpStoreLocatorSpider
from locations.storefinders.localisr import LocalisrSpider
from locations.storefinders.locally import LocallySpider
from locations.storefinders.maps_marker_pro import MapsMarkerProSpider
from locations.storefinders.metalocator import MetaLocatorSpider
from locations.storefinders.metizsoft import MetizsoftSpider
from locations.storefinders.momentfeed import MomentFeedSpider
from locations.storefinders.rio_seo import RioSeoSpider

# from locations.storefinders.rexel import RexelSpider
from locations.storefinders.shopapps import ShopAppsSpider
from locations.storefinders.stockinstore import StockInStoreSpider
from locations.storefinders.stockist import StockistSpider
from locations.storefinders.store_locator_plus_cloud import StoreLocatorPlusCloudSpider
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider
from locations.storefinders.storemapper import StoremapperSpider
from locations.storefinders.storepoint import StorepointSpider
from locations.storefinders.storerocket import StoreRocketSpider
from locations.storefinders.super_store_finder import SuperStoreFinderSpider
from locations.storefinders.sweetiq import SweetIQSpider
from locations.storefinders.sylinder import SylinderSpider
from locations.storefinders.uberall import UberallSpider
from locations.storefinders.virtualearth import VirtualEarthSpider
from locations.storefinders.where2getit import Where2GetItSpider
from locations.storefinders.woosmap import WoosmapSpider
from locations.storefinders.wp_go_maps import WpGoMapsSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider
from locations.storefinders.yext import YextSpider
from locations.storefinders.yext_answers import YextAnswersSpider

# from locations.storefinders.yext_search import YextSearchSpider
from locations.user_agents import BROWSER_DEFAULT


class StorefinderDetectorSpider(Spider):
    name = "storefinder_detector"
    start_urls = []
    custom_settings = {
        "COOKIES_ENABLED": True,
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "firefox_user_prefs": {
                # Prevent browser popups asking for permissions to
                # be granted. These popups if ignored will block
                # JavaScript functions on the page from completing,
                # leading to the page only partially loading dynamic
                # content.
                # Values:
                #   1 = always allow permission
                #       (needed to allow presentation of fake
                #        geolocation data to any page that asks)
                #   2 = always deny permission
                "permissions.default.camera": 2,
                "permissions.default.desktop-notification": 2,
                "permissions.default.geo": 1,
                "permissions.default.microphone": 2,
                "permissions.default.xr": 2,
            },
            # For debugging purposes, disable headless mode so that
            # any problems preventing a complete page load are
            # easily determined.
            # "headless": False
            #
            # If https://github.com/microsoft/playwright/issues/7297
            # is ever implemented, uBlock Origin would be useful to
            # enable here.
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }
    user_agent = BROWSER_DEFAULT
    parameters: dict = {
        "brand": None,
        "brand_wikidata": None,
        "operator": None,
        "operator_wikidata": None,
        "spider_key": "new_brand_zz",
        "spider_class_name": "NewBrandZZSpider",
    }
    detected_storefinders: dict = {}

    def __init__(
        self,
        url: str = None,
        brand_wikidata: str = None,
        operator_wikidata: str = None,
        spider_key: str = None,
        spider_class_name: str = None,
        *args,
        **kwargs,
    ):
        self.start_urls = [url]
        self.brand_wikidata = brand_wikidata
        self.operator_wikidata = operator_wikidata
        self.spider_key = spider_key
        self.spider_class_name = spider_class_name
        self.automatically_set_parameters()

    def automatically_set_brand_or_operator_from_start_url(self):
        """
        Automatically extract parameters["brand_wikidata"] or
        parameters["operator_wikidata"] from a supplied
        start_urls[0]. Name Suggestion Index data is searched to find
        an entry that has the same domain name as start_urls[0]. If
        a match is found, parameters["brand_wikidata"] or
        parameters["operator_wikidata"] are automatically set.
        """
        if not self.parameters["brand_wikidata"] and not self.parameters["operator_wikidata"] and self.start_urls:
            nsi = NSI()
            wikidata_code = nsi.get_wikidata_code_from_url(self.start_urls[0])
            if wikidata_code:
                nsi_matches = [nsi_match for nsi_match in nsi.iter_nsi(wikidata_code)]
                if len(nsi_matches) == 1:
                    if "brand:wikidata" in nsi_matches[0]["tags"].keys():
                        self.parameters["brand_wikidata"] = wikidata_code
                    elif "operator:wikidata" in nsi_matches[0]["tags"].keys():
                        self.parameters["operator_wikidata"] = wikidata_code

    def automatically_set_parameters(self):
        """
        Automatically extract parameters from at least one or more
        of the following:
          1. start_urls[0]
          2. parameters["brand_wikidata"]
          3. parameters["operator_wikidata"]

        If any of the above are specified for this spider, and this
        method is called, this method will attempt to populate all
        other parameters automatically from Name Suggestion Index
        data.

        See automatically_set_brand_or_operator_from_start_url(self)
        for details on how parameters are extracted from just a single
        supplied start_urls[0].
        """
        if not self.parameters["brand_wikidata"] and not self.parameters["operator_wikidata"]:
            self.automatically_set_brand_or_operator_from_start_url()

        nsi = NSI()
        if self.parameters["brand_wikidata"] or self.parameters["operator_wikidata"]:
            wikidata_code = self.parameters["brand_wikidata"] or self.parameters["operator_wikidata"]
            nsi_matches = [nsi_match for nsi_match in nsi.iter_nsi(wikidata_code)]
            if len(nsi_matches) != 1:
                return

            if found_keys := NSI.generate_keys_from_nsi_attributes(nsi_matches[0]):
                self.parameters["spider_key"] = found_keys[0]
                self.parameters["spider_class_name"] = found_keys[1]

            if self.parameters["brand_wikidata"]:
                brand = nsi_matches[0]["tags"].get("brand", nsi_matches[0]["tags"].get("name"))
                self.parameters["brand"] = brand
            elif self.parameters["operator_wikidata"]:
                operator = nsi_matches[0]["tags"].get("operator", nsi_matches[0]["tags"].get("name"))
                self.parameters["operator"] = operator

    @staticmethod
    def get_all_storefinders() -> list[type[AutomaticSpiderGenerator]]:
        all_storefinders = [
            # Only storefinders with functioning automatic
            # storefinder detection and automatic spider generation
            # are enabled below. The remainder are work in progress
            # to enable.
            AheadworksSpider,
            AlgoliaSpider,
            AgileStoreLocatorSpider,
            AmastyStoreLocatorSpider,
            AmrestEUSpider,
            ClosebySpider,
            EasyLocatorSpider,
            FreshopSpider,
            GeoMeSpider,
            KiboSpider,
            LighthouseSpider,
            LimesharpStoreLocatorSpider,
            LocalisrSpider,
            LocallySpider,
            MapsMarkerProSpider,
            MetaLocatorSpider,
            MetizsoftSpider,
            MomentFeedSpider,
            # RexelSpider,
            RioSeoSpider,
            ShopAppsSpider,
            StockInStoreSpider,
            StockistSpider,
            StorefrontgatewaySpider,
            StoreLocatorPlusCloudSpider,
            StoreLocatorPlusSelfSpider,
            StoreLocatorWidgetsSpider,
            StoremapperSpider,
            StorepointSpider,
            StoreRocketSpider,
            SuperStoreFinderSpider,
            SweetIQSpider,
            SylinderSpider,
            UberallSpider,
            VirtualEarthSpider,
            Where2GetItSpider,
            WoosmapSpider,
            WpGoMapsSpider,
            WPStoreLocatorSpider,
            YextSpider,
            YextAnswersSpider,
            # YextSearchSpider,
        ]
        return all_storefinders

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            # Load the page in a Playwright browser so that storefinder
            # classes can interrogate the same page in turn without
            # having to re-request the same page.
            meta = {
                "playwright": True,
                "playwright_context": "atp_storefinder_detector",
                "playwright_context_kwargs": {
                    # Fake geolocation data to any page that may
                    # expect to retrieve geolocation data from the
                    # browser. Failure to automatically provide this
                    # geolocation data to some storefinder pages
                    # will prevent those pages from loading
                    # successfully.
                    "geolocation": {"latitude": 0, "longitude": 0},
                    "permissions": ["geolocation"],
                },
                "playwright_include_page": True,
                "playwright_page_event_handlers": {
                    "request": "handle_storefinder_page_request",
                },
            }
            yield Request(url=url, meta=meta, errback=self.errback_close_page)

            # Also give storefinder classes the opportunity to customise
            # requests to storefinder pages should this be necessary.
            # This could include needing to register Playwright handlers
            # for interacting with the storefinder page (e.g. to click a
            # button that may appear).
            all_storefinders = self.get_all_storefinders()
            for storefinder in all_storefinders:
                if not issubclass(storefinder, AutomaticSpiderGenerator):
                    continue
                for custom_request in storefinder.request_storefinder_page(url):
                    if custom_request is not None:
                        yield custom_request

    @staticmethod
    def retype_parameters_dict(raw_dict: dict) -> dict:
        retyped_parameters = {}
        for k, v in raw_dict.items():
            if k.endswith("__list"):
                retyped_parameters[k.replace("__list", "")] = [v]
            else:
                retyped_parameters[k] = v
        return retyped_parameters

    @staticmethod
    def execute_jq(query: str, input_data: dict | str) -> dict | bool:
        result = jq.compile(query).input_value(input_data).first()
        if not isinstance(result, dict) and not isinstance(result, bool):
            # The query should only return a dictionary of extracted
            # parameters, or a boolean value of True if the query
            # was a success and no parameters needed extracting.
            # Any other return value from the query is considered
            # a failure.
            return False
        if isinstance(result, dict):
            if not result:
                # Empty dictionaries occur when a parameter was
                # expected to be extracted, but wasn't. A return of
                # "False" as a boolean value makes it clear the
                # query failed.
                return False
            for k, v in result.items():
                if v is None:
                    # A dictionary item value of None indicates that
                    # a parameter was expected to be extracted, but
                    # no value was successfully extracted. If the
                    # caller needs to verify a field in input data
                    # is null/None, the query should return a
                    # boolean value of True if a null/None value was
                    # successfully found as expected.
                    return False
        return result

    def add_parameters(self, storefinder: type[AutomaticSpiderGenerator], parameters: dict) -> None:
        if storefinder.__name__ not in self.detected_storefinders.keys():
            self.detected_storefinders[storefinder.__name__] = {}
        self.detected_storefinders[storefinder.__name__].update(parameters)

    async def handle_storefinder_page_request(self, request: PlaywrightRequest) -> None:
        all_storefinders = self.get_all_storefinders()
        for storefinder in all_storefinders:
            for detection_rule in filter(
                lambda x: isinstance(x, DetectionRequestRule) and x, storefinder.detection_rules
            ):
                extracted_parameters = {}

                # Perform a regular expression match against the request URL.
                if url_regex := detection_rule.url:
                    if m := re.search(url_regex, request.url):
                        retyped_parameters = StorefinderDetectorSpider.retype_parameters_dict(m.groupdict())
                        extracted_parameters.update(retyped_parameters)
                    else:
                        continue

                # Conduct a JQ query against the HTTP headers sent with the
                # request. HTTP headers are first converted into a JSON
                # dictionary allowing JQ to be used for querying.
                if headers_jq := detection_rule.headers:
                    if headers_result := self.execute_jq(headers_jq, request.headers):
                        if isinstance(headers_result, dict):
                            extracted_parameters.update(headers_result)
                    else:
                        continue

                # Conduct a JQ query against the URL-encoded or JSON-encoded
                # POST data sent with the request. If URL-encoding is used,
                # the POST data is first converted into a JSON dictionary
                # allowing JQ to be used for querying. If the request is sent
                # with multi-part encoding, this data is ignored as support
                # for converting multi-part encoding to a JSON dictionary
                # is not implemented.
                if post_data_jq := detection_rule.data:
                    if "content-type" not in request.headers.keys():
                        continue
                    if request.headers["content-type"].split(";", 1)[0] not in [
                        "application/json",
                        "application/x-www-form-urlencoded",
                    ]:
                        continue

                    # Workaround for playwright-python bug https://github.com/microsoft/playwright-python/issues/2348
                    post_data_json = {}
                    if request.headers["content-type"].startswith("application/x-www-form-urlencoded"):
                        post_data_json = dict(parse_qsl(request.post_data))
                    else:
                        post_data_json = request.post_data_json

                    if post_data_result := self.execute_jq(post_data_jq, post_data_json):
                        if isinstance(post_data_result, dict):
                            extracted_parameters.update(post_data_result)
                    else:
                        continue

                self.add_parameters(storefinder, extracted_parameters)

    async def handle_storefinder_page_response(self, response: Response) -> None:
        all_storefinders = self.get_all_storefinders()
        for storefinder in all_storefinders:
            for detection_rule in filter(
                lambda x: isinstance(x, DetectionResponseRule) and x, storefinder.detection_rules
            ):
                extracted_parameters = {}

                # Perform a regular expression match against the URL of the
                # main frame. Note that the URLs of iframes are ignored.
                if url_regex := detection_rule.url:
                    if m := re.search(url_regex, response.url):
                        retyped_parameters = StorefinderDetectorSpider.retype_parameters_dict(m.groupdict())
                        extracted_parameters.update(retyped_parameters)
                    else:
                        continue

                # Conduct a JQ query against the HTTP headers returned for the
                # main frame. HTTP headers are first converted into a JSON
                # dictionary allowing JQ to be used for querying. Note that
                # headers of iframes are ignored.
                if headers_jq := detection_rule.headers:
                    if headers_result := self.execute_jq(headers_jq, response.headers):
                        if isinstance(headers_result, dict):
                            extracted_parameters.update(headers_result)
                    else:
                        continue

                # Execute JavaScript code in the main frame and then all
                # nested iframes in order of their appearance in the DOM for
                # the provided JS code. The search stops as soon as the first
                # non-null response is received. Exceptions will cause a null
                # response.
                remaining_js_objects = deepcopy(detection_rule.js_objects)
                for param_name, js_code in detection_rule.js_objects.items():
                    page = response.meta["playwright_page"]
                    result = await self.extract_javascript_object(js_code, page.main_frame)
                    if result is None:
                        break
                    if not param_name.startswith("__"):
                        extracted_parameters.update({param_name: result})
                    remaining_js_objects.pop(param_name)
                if len(remaining_js_objects.keys()) != 0:
                    continue

                # Search the main frame and then all nested iframes in order
                # of their appearance in the DOM for an XPath query provided.
                # The search stops as soon as the first XPath query succeeds.
                remaining_xpaths = deepcopy(detection_rule.xpaths)
                for param_name, xpath in detection_rule.xpaths.items():
                    page = response.meta["playwright_page"]
                    result = await self.extract_xpath_object(xpath, page.main_frame)
                    if result is None:
                        break
                    if len(result) > 1 and not param_name.endswith("__list"):
                        break
                    elif len(result) == 1 and not param_name.endswith("__list"):
                        result = result[0]
                    if not param_name.startswith("__"):
                        extracted_parameters.update({param_name: result})
                    remaining_xpaths.pop(param_name)
                if len(remaining_xpaths.keys()) != 0:
                    continue

                self.add_parameters(storefinder, extracted_parameters)

    async def extract_javascript_object(self, js_code: str, frame: Frame) -> Any:
        try:
            return await frame.evaluate("() => " + js_code)
        except:
            for child_frame in frame.child_frames:
                if not child_frame.url.startswith("https://") and not child_frame.url.startswith("http://"):
                    continue
                result = await self.extract_javascript_object(js_code, child_frame)
                if result is not None:
                    return result
            return None

    async def extract_xpath_object(self, xpath: str, frame: Frame) -> Any:
        frame_content = None
        try:
            frame_content = await frame.content()
        except:
            # frame.child_frames has been observed to contain duplicate
            # iframes, causing an error:
            #   playwright._impl._api_types.Error: Execution context was
            #   destroyed, most likely because of a navigation
            # The second of the duplicate frames does allow content to be
            # returned, so the error appears to be OK to ignore on the first
            # of the duplicate frames.
            # Unsure why this error occurs and frames appear duplicated.
            return None
        if not frame_content:
            return None
        if result := list(filter(None, Selector(text=frame_content).xpath(xpath).getall())):
            return result
        else:
            for child_frame in frame.child_frames:
                if not child_frame.url.startswith("https://") and not child_frame.url.startswith("http://"):
                    continue
                result = await self.extract_xpath_object(xpath, child_frame)
                if result is not None:
                    return result
            return None

    async def parse(self, response: Response) -> Any:
        page = response.meta["playwright_page"]
        # Perform some very basic page actions with the mouse to
        # pretend to be viewing the page. This may be required to
        # trigger some dynamic content on the page to load.
        # Additionally wait a few seconds for any obfuscated
        # JavaScript blobs to execute after DOM loading is complete.
        # We don't know what we're waiting for because the API calls
        # we want to observe are potentially hidden in obfuscated
        # JavaScript blobs that could take a while to execute.
        await page.wait_for_timeout(1000)
        await page.mouse.move(0, 0)
        await page.mouse.move(100, 100)
        await page.wait_for_timeout(1000)
        await page.mouse.wheel(100, 100)
        await page.wait_for_timeout(3000)
        await self.handle_storefinder_page_response(response)
        await page.close()
        for storefinder_name, storefinder_attributes in self.detected_storefinders.items():
            storefinder = [x for x in self.get_all_storefinders() if x.__name__ == storefinder_name]
            if len(storefinder) != 1:
                break
            new_spider = type(
                self.parameters["spider_class_name"],
                (storefinder[0],),
                {"__module__": "locations.spiders"},
                response=response,
                brand_wikidata=self.parameters["brand_wikidata"],
                brand=self.parameters["brand"],
                operator_wikidata=self.parameters["operator_wikidata"],
                operator=self.parameters["operator"],
                spider_key=self.parameters["spider_key"],
                extracted_attributes=storefinder_attributes,
            )
            generated_spider = GeneratedSpider()
            generated_spider["storefinder_url"] = response.url
            generated_spider["spider"] = new_spider
            yield generated_spider

    async def errback_close_page(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
