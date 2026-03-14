import re
from typing import Any, Iterable

import chompjs
from scrapy.http import Response, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VerizonUSSpider(CrawlSpider, StructuredDataSpider):
    name = "verizon_us"
    item_attributes = {"brand": "Verizon", "brand_wikidata": "Q919641"}
    start_urls = ["https://www.verizon.com/nextgendigital/nos/storelocator"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/storelocator/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"/storelocator/[-\w]+/[-\w]+$"), callback="parse"),
    ]

    OPERATORS = {
        "Asurion FSL": {"operator": "Asurion FSL"},
        "BeMobile": {"operator": "BeMobile"},
        "Best Buy": {"operator": "Best Buy", "operator_wikidata": "Q533415"},
        "Best Wireless": {"operator": "Best Wireless"},
        "Cellular Plus": {"operator": "Cellular Plus"},
        "Cellular Sales": {"operator": "Cellular Sales", "operator_wikidata": "Q5058345"},
        "Mobile Generation": {"operator": "Mobile Generation"},
        "R Wireless": {"operator": "R Wireless"},
        "Russell Cellular": {"operator": "Russell Cellular", "operator_wikidata": "Q125523800"},
        "TCC": {"operator": "The Cellular Connection", "operator_wikidata": "Q121336519"},
        "Team Wireless": {"operator": "Team Wireless"},
        "Victra": {"operator": "Victra", "operator_wikidata": "Q118402656"},
        "Wireless Plus": {"operator": "Wireless Plus"},
        "Wireless World": {"operator": "Wireless World"},
        "Wireless Zone": {"operator": "Wireless Zone", "operator_wikidata": "Q122517436"},
        "Your Wireless": {"operator": "Your Wireless"},
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_url in re.findall(r'\\"storeUrl\\":\\"(.+?)\\"', response.text):
            if "/details/" not in store_url:
                store_url = store_url.replace("/stores/", "/stores/details/")
            yield response.follow(url=store_url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url
        store_data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "storeJSON")]/text()').get())
        item["ref"] = store_data["storeNumber"]
        item["name"] = store_data["storeName"]

        if "Authorized Retailer" in store_data["typeOfStore"]:
            for operator, tags in self.OPERATORS.items():
                if item["name"].startswith(operator):
                    item["branch"] = item.pop("name").removeprefix(operator).strip(" -")
                    item.update(tags)
                    break
        else:
            item["branch"] = item.pop("name")
            item["operator"] = self.item_attributes["brand"]
            item["operator_wikidata"] = self.item_attributes["brand_wikidata"]

        if item.get("branch") and "#" in item["branch"]:
            item["branch"] = item["branch"].split("#")[1].split(" ", 1)[-1]

        #  ld_data hours don't match with Google Maps data, hence skipped.
        item["opening_hours"] = self.parse_hours(store_data.get("StoreHours"))

        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item

    def parse_hours(self, store_hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS_3_LETTERS:
            opening_hours.add_range(day, store_hours.get(f"{day}Open"), store_hours.get(f"{day}Close"), "%I:%M %p")
        return opening_hours
