import html
import json

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AccentureSpider(scrapy.Spider):
    name = "accenture"
    item_attributes = {"brand": "Accenture", "brand_wikidata": "Q338825"}
    start_urls = ["https://www.accenture.com/us-en/about/location"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def parse(self, response, **kwargs):
        for country in response.xpath('//a[contains(@class, "cmp-text__link")]/text()').getall():
            yield JsonRequest(
                url=f"https://www.accenture.com/us-en/about/locations/office-details/jcr:content/root/container_main/locationhero_copy.result.html?query={country}&from=0&size=1500",
                callback=self.parse_country,
            )

    def parse_country(self, response, **kwargs):
        for office in json.loads(html.unescape(response.text)):
            item = DictParser.parse(office)
            item.pop("state")
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["brand"]
            item["street_address"] = item.pop("addr_full")
            item["postcode"] = office.get("postalZipCode", "")
            item["phone"] = office.get("contactTel", "")
            apply_category(Categories.OFFICE_CONSULTING, item)
            yield item
