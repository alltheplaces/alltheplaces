import json
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# Official documentation for Agile Store Locator:
# https://agilestorelocator.com/documentation/
#
# To use this store finder, specify allowed_domains = [x, y, ..]
# (either one or more domains such as example.net) and the default
# path for the Agile Store Locator API endpoint will be used.
# In the event the default path is different, you can alternatively
# specify one or more start_urls = [x, y, ..].
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (an ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).


class AgileStoreLocatorSpider(Spider):
    def start_requests(self):
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                yield JsonRequest(url=f"https://{domain}/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1")
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            item["name"] = item["name"].strip()
            item["street_address"] = item.pop("street")
            hours_json = json.loads(location["open_hours"])
            for day_name, hours_ranges in hours_json.items():
                for hours_range in hours_ranges:
                    hours_range = hours_range.upper()
                    if not hours_range or hours_range == "0":
                        continue
                    if hours_range == "1":
                        start_time = "12:00 AM"
                        end_time = "11:59 PM"
                    else:
                        start_time = hours_range.split(" - ", 1)[0]
                        end_time = hours_range.split(" - ", 1)[1]
                    if "AM" in start_time or "PM" in start_time or "AM" in end_time or "PM" in end_time:
                        item["opening_hours"].add_range(DAYS_EN[day_name.title()], start_time, end_time, "%I:%M %p")
                    else:
                        item["opening_hours"].add_range(DAYS_EN[day_name.title()], start_time, end_time)
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item

    @staticmethod
    def storefinder_exists(response: Response) -> bool:
        if len(response.xpath('//*[contains(@id, "agile-store-locator-")]')) > 0:
            return True
        return False

    def __init_subclass__(cls, **kwargs):
        if "response" in kwargs.keys() and kwargs["response"] and isinstance(kwargs["response"], Response):
            cls.allowed_domains = [urlparse(kwargs["response"].url).netloc]
        if "brand_wikidata" in kwargs.keys() and kwargs["brand_wikidata"]:
            cls.item_attributes = {}
            cls.item_attributes["brand_wikidata"] = kwargs["brand_wikidata"]
            if "brand" in kwargs.keys() and kwargs["brand"]:
                cls.item_attributes["brand"] = kwargs["brand"]
        if "spider_key" in kwargs.keys() and kwargs["spider_key"]:
            cls.name = kwargs["spider_key"]

    @staticmethod
    def generate_spider_code(spider: Spider) -> str:
        imports_list = ""
        superclasses = []
        for spider_base in spider.__bases__:
            imports_list = "{}from {} import {}\n".format(imports_list, spider_base.__module__, spider_base.__name__)
            superclasses.append(spider_base.__name__)
        superclasses_list = ", ".join(superclasses)

        spider_key_code = ""
        if hasattr(spider, "name") and isinstance(spider.name, str):
            spider_key_code = '\tname = "{}"\n'.format(spider.name)

        item_attributes_code = ""
        if (
            hasattr(spider, "item_attributes")
            and isinstance(spider.item_attributes, dict)
            and "brand_wikidata" in spider.item_attributes.keys()
        ):
            if "brand" in spider.item_attributes.keys():
                item_attributes_code = '\titem_attributes = {{"brand": "{}", "brand_wikidata": "{}"}}\n'.format(
                    spider.item_attributes["brand"], spider.item_attributes["brand_wikidata"]
                )
            else:
                item_attributes_code = '\titem_attributes = {{"brand_wikidata": "{}"}}\n'.format(
                    spider.item_attributes["brand_wikidata"]
                )

        allowed_domains_code = ""
        if (
            hasattr(spider, "allowed_domains")
            and len(spider.allowed_domains) == 1
            and isinstance(spider.allowed_domains[0], str)
        ):
            allowed_domains_code = '\tallowed_domains = ["{}"]\n'.format(spider.allowed_domains[0])

        spider_code = "{}\n\nclass {}({}):\n{}{}{}".format(
            imports_list,
            spider.__name__,
            superclasses_list,
            spider_key_code,
            item_attributes_code,
            allowed_domains_code,
        )
        return spider_code
