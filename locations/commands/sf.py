import inspect
import re
import sys

import pycountry
from scrapy import Spider
from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.name_suggestion_index import NSI
from locations.storefinders import *
from locations.user_agents import BROWSER_DEFAULT


class DetectorSpider(Spider):
    name = "detector_spider"
    start_urls = []
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT
    parameters = {
        "brand": None,
        "brand_wikidata": None,
        "operator": None,
        "operator_wikidata": None,
        "spider_key": None,
        "spider_class_name": "NewBrandZZSpider",
    }

    def parse(self, response):
        for storefinder in [
            cls
            for _, cls in inspect.getmembers(sys.modules["locations.storefinders"], inspect.isclass)
            if [base for base in cls.__bases__ if base.__name__ == AutomaticSpiderGenerator.__name__]
        ]:
            if not storefinder.storefinder_exists(response):
                continue
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
                extracted_attributes=storefinder.extract_spider_attributes(response),
            )
            if not callable(getattr(storefinder, "generate_spider_code")):
                break
            print(storefinder.generate_spider_code(new_spider))
            break


# Detect presence of a store finder at a given URL, and return a pre-filled Spider.
class SfCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_LEVEL": "WARNING"}

    def syntax(self):
        return "[options] <URL to scan for store finder>"

    def short_desc(self):
        return "Detect presence of a store finder at a given URL, and return a pre-filled Spider"

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--brand-wikidata",
            dest="brand_wikidata",
            help="attempt to pre-fill brand name and NSI category based on supplied Wikidata Q-code",
        )
        parser.add_argument(
            "--operator-wikidata",
            dest="operator_wikidata",
            help="attempt to pre-fill operator name and NSI category based on supplied Wikidata Q-code",
        )
        parser.add_argument(
            "--spider-key",
            dest="spider_key",
            help="pre-fill a spider key (should match the desired file name for the spider with optionally one or more _xx suffixes where xx is an ISO 3166-2 code)",
        )
        parser.add_argument(
            "--spider-class-name",
            dest="spider_class_name",
            help="pre-fill a spider class name (should be in title case and suffixed with 'Spider')",
        )

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify single URL that is desired to be scanned for a store finder.")

        if not args[0].startswith("http"):
            raise UsageError(
                "A http or https URL scheme is required when specifying the single URL that is desired to be scanned for a store finder."
            )

        nsi = NSI()

        if opts.brand_wikidata:
            DetectorSpider.parameters["brand_wikidata"] = opts.brand_wikidata
        elif opts.operator_wikidata:
            DetectorSpider.parameters["operator_wikidata"] = opts.operator_wikidata
        else:
            wikidata_code = nsi.get_wikidata_code_from_url(args[0])
            if wikidata_code:
                nsi_matches = [nsi_match for nsi_match in nsi.iter_nsi(wikidata_code)]
                if len(nsi_matches) == 1:
                    if "brand:wikidata" in nsi_matches[0]["tags"].keys():
                        DetectorSpider.parameters["brand_wikidata"] = wikidata_code
                    elif "operator:wikidata" in nsi_matches[0]["tags"].keys():
                        DetectorSpider.parameters["operator_wikidata"] = wikidata_code

        if DetectorSpider.parameters["brand_wikidata"] or DetectorSpider.parameters["operator_wikidata"]:
            wikidata_code = (
                DetectorSpider.parameters["brand_wikidata"] or DetectorSpider.parameters["operator_wikidata"]
            )
            nsi_matches = [nsi_match for nsi_match in nsi.iter_nsi(wikidata_code)]
            if len(nsi_matches) == 1:
                spider_key = re.sub(r"[^a-zA-Z0-9_]", "", nsi_matches[0]["tags"]["name"].replace(" ", "_")).lower()
                spider_class_name = re.sub(r"[^a-zA-Z0-9]", "", nsi_matches[0]["tags"]["name"].replace(" ", ""))
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
                DetectorSpider.parameters["spider_key"] = spider_key
                DetectorSpider.parameters["spider_class_name"] = spider_class_name
                if DetectorSpider.parameters["brand_wikidata"]:
                    brand = nsi_matches[0]["tags"].get("brand", nsi_matches[0]["tags"].get("name"))
                    DetectorSpider.parameters["brand"] = brand
                elif DetectorSpider.parameters["operator_wikidata"]:
                    operator = nsi_matches[0]["tags"].get("operator", nsi_matches[0]["tags"].get("name"))
                    DetectorSpider.parameters["operator"] = operator

        if opts.spider_key:
            DetectorSpider.parameters["spider_key"] = opts.spider_key

        if opts.spider_class_name:
            DetectorSpider.parameters["spider_class_name"] = opts.spider_class_name

        DetectorSpider.start_urls = [args[0]]

        crawler = self.crawler_process.create_crawler(DetectorSpider)
        self.crawler_process.crawl(crawler)
        self.crawler_process.start()
