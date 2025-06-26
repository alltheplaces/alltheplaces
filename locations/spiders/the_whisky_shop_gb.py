import json
import re

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from scrapy import Spider
from locations.pipelines.address_clean_up import merge_address_lines


class TheWhiskyShopGBSpider(Spider):
    name = "the_whisky_shop_gb"
    item_attributes = {"brand": "The Whisky Shop", "brand_wikidata": "Q134400495"}
    start_urls = ["https://www.whiskyshop.com/shops"]

    def parse(self, response):
        match = re.search(r'{"shops":([^\n]+),"styles":', response.text)
        data = match.group(1)
        json_data = json.loads(data)
        for location in json_data.values():
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
            item["branch"] = item.pop("name").removeprefix("The Whisky Shop ")
            oh = OpeningHours()
            for day in DAYS_FULL:
                myday = location["normal_hours"][day]
                oh.add_range(day, myday["from"], myday["to"])
            item["opening_hours"] = oh
            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
