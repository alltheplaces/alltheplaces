from scrapy import Spider

from locations.categories import apply_yes_no, Extras
from locations.dict_parser import DictParser
import json
import re


class MaxSpider(Spider):
    name = "max"
    item_attributes = {"brand": "Max", "brand_wikidata": "Q1912172"}
    start_urls = ["https://www.max.se/hitta-max/restauranger/"]
    no_refs = True

    def parse(self, response, **kwargs):
        raw_data = response.xpath("//div[@data-app='RestaurantList']").get()
        for location in (json.loads(re.search(r'"restaurants":\s*(.*?),\s*"i18n"', raw_data).group(1))):
            item = DictParser.parse(location)
            item["postcode"] = location["postalCode"].strip(location["city"]).strip()
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveIn"])

            yield item

