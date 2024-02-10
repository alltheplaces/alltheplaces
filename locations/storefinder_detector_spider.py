import inspect
import re
import sys

import pycountry
from scrapy import Spider
from scrapy.http import Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.items import GeneratedSpider
from locations.name_suggestion_index import NSI
from locations.storefinders import *
from locations.user_agents import BROWSER_DEFAULT


class StorefinderDetectorSpider(Spider):
    name = "storefinder_detector"
    start_urls = []
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }
    user_agent = BROWSER_DEFAULT
    parameters = {
        "brand": None,
        "brand_wikidata": None,
        "operator": None,
        "operator_wikidata": None,
        "spider_key": "new_brand_zz",
        "spider_class_name": "NewBrandZZSpider",
    }

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
        # TODO: For running stand alone, this makes sense.
        # For invoking from other areas - where we may already have a lot of this information, this work in the constructor doubles efforts
        # Consider shifting up to the caller
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
            spider_key = re.sub(r"[^a-zA-Z0-9_]", "", nsi_matches[0]["tags"]["name"].replace(" ", "_")).lower()
            spider_class_name = re.sub(r"[^a-zA-Z0-9]", "", nsi_matches[0]["tags"]["name"].replace(" ", ""))

            # Add country name to spider name if spider exists in a single country
            if nsi_matches[0].get("locationSet") and nsi_matches[0]["locationSet"].get("include"):
                if (
                    len(nsi_matches[0]["locationSet"]["include"]) == 1
                    or len(nsi_matches[0]["locationSet"]["include"]) == 2
                ):
                    for country_code in nsi_matches[0]["locationSet"]["include"]:
                        if not pycountry.countries.get(alpha_2=country_code.upper()):
                            continue
                        spider_key = f"{spider_key}_{country_code.lower()}"
                        spider_class_name = f"{spider_class_name}{country_code.upper()}"

            spider_class_name = f"{spider_class_name}Spider"
            self.parameters["spider_key"] = spider_key
            self.parameters["spider_class_name"] = spider_class_name
            if self.parameters["brand_wikidata"]:
                brand = nsi_matches[0]["tags"].get("brand", nsi_matches[0]["tags"].get("name"))
                self.parameters["brand"] = brand
            elif self.parameters["operator_wikidata"]:
                operator = nsi_matches[0]["tags"].get("operator", nsi_matches[0]["tags"].get("name"))
                self.parameters["operator"] = operator

    def parse(self, response: Response):
        all_storefinders = [
            storefinder
            for storefinder in [
                cls
                for _, cls in inspect.getmembers(sys.modules["locations.storefinders"], inspect.isclass)
                if [base for base in cls.__bases__ if base.__name__ == AutomaticSpiderGenerator.__name__]
            ]
        ]
        detection_results = [
            (storefinder, storefinder.storefinder_exists(response)) for storefinder in all_storefinders
        ]
        detected_storefinders = [storefinder[0] for storefinder in detection_results if storefinder[1] is True]
        for detected_storefinder in detected_storefinders:
            response.meta["storefinder"] = detected_storefinder
            response.meta["first_response"] = response
            response.meta["first_response"].meta["storefinder"] = detected_storefinder
            yield from self.parse_detection(response)
        additional_requests = [result for result in detection_results if isinstance(result[1], Request)]
        for additional_request in additional_requests:
            additional_request[1].meta["storefinder"] = additional_request[0]
            additional_request[1].meta["first_response"] = response
            additional_request[1].meta["first_response"].meta["storefinder"] = additional_request[0]
            additional_request[1].callback = self.parse_detection
            yield additional_request[1]

    def parse_detection(self, response: Response):
        storefinder = response.meta["storefinder"]
        next_detection_method = response.meta.get("next_detection_method", storefinder.storefinder_exists)
        storefinder_exists = next_detection_method(response)
        if isinstance(storefinder_exists, Request):
            storefinder_exists.meta["storefinder"] = storefinder
            storefinder_exists.meta["first_response"] = response.meta.get("first_response")
            storefinder_exists.callback = self.parse_detection
            yield storefinder_exists
            return
        if storefinder_exists is True:
            yield from self.parse_extraction(response.meta["first_response"]) # TODO: Check if first_response is right, or if it should be last_response. When running multiple times for multiple stores, I was seeing the current url with the first generated spider 

    def parse_extraction(self, response: Response):
        storefinder = response.meta["storefinder"]
        next_extraction_method = response.meta.get("next_extraction_method", storefinder.extract_spider_attributes)
        spider_attributes = next_extraction_method(response)
        if isinstance(spider_attributes, Request):
            spider_attributes.meta["storefinder"] = storefinder
            spider_attributes.callback = self.parse_extraction
            yield spider_attributes
            return
        new_spider = type(
            self.parameters["spider_class_name"],
            (storefinder,),
            {"__module__": "locations.spiders"},
            response=response,
            brand_wikidata=self.parameters["brand_wikidata"],
            brand=self.parameters["brand"],
            operator_wikidata=self.parameters["operator_wikidata"],
            operator=self.parameters["operator"],
            spider_key=self.parameters["spider_key"],
            extracted_attributes=spider_attributes,
        )
        generated_spider = GeneratedSpider()
        generated_spider["search_url"] = response.url
        generated_spider["spider"] = new_spider
        yield generated_spider
