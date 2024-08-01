from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class VinceSpider(Spider):
    name = "vince"
    item_attributes = {"brand": "VINCE.", "brand_wikidata": "Q7907025"}
    start_urls = [
        "https://www.vince.com/on/demandware.store/Sites-vince-Site/default/Stores-FindStores?radius=20000&lat=0&long=0"
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)

            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["branch"] = item.pop("name").removeprefix("Vince ")

            oh = OpeningHours()
            for line in (location["fullStoreHours"] or "").split("<br/>"):
                oh.add_ranges_from_string(line)
            item["opening_hours"] = oh

            yield item
