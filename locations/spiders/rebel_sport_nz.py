import json
import re

from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RebelSportNZSpider(Spider):
    name = "rebel_sport_nz"
    item_attributes = {"brand": "Rebel Sport", "brand_wikidata": "Q110190372"}
    allowed_domains = ["www.rebelsport.co.nz"]
    start_urls = ["https://www.rebelsport.co.nz/"]

    def parse(self, response):
        locations = []
        store_lists = response.xpath("//@data-store").getall()
        for store_list_str in store_lists:
            store_list = json.loads(store_list_str)
            locations = locations + store_list
        for location in locations:
            item = DictParser.parse(location)
            item.pop("addr_full", None)
            item["street_address"] = re.sub(
                r"\s+",
                " ",
                " ".join(Selector(text="<div>" + location["address"] + "</div>").xpath("//div/text()").getall()),
            ).strip()
            item["phone"] = Selector(text=location["telephone"]).xpath("//@href").get().replace("tel:", "")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["hours"])
            yield item
