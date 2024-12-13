import json
import re

from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class MaxSpider(Spider):
    name = "max"
    item_attributes = {"brand": "Max", "brand_wikidata": "Q1912172"}
    no_refs = True

    def start_requests(self):
        start_urls = {
            "SE": "https://www.max.se/hitta-max/restauranger/",
            "DK": "https://www.max.dk/find-max/restauranter/",
            "NO": "https://www.maxhamburger.no/finn-max/finn-max/",
            "PL": "https://www.maxpremiumburgers.pl/znajdz-max/restauracje/",
        }
        for country, url in start_urls.items():
            yield Request(url, cb_kwargs={"country": country})

    def parse(self, response, country=None):
        raw_data = response.xpath("//div[@data-app='RestaurantList']").get()
        for location in json.loads(re.search(r'"restaurants":\s*(.*?),\s*"i18n"', raw_data).group(1)):
            item = DictParser.parse(location)
            item["postcode"] = location["postalCode"].strip(location["city"]).strip()
            item["country"] = country
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveIn"])

            yield item
