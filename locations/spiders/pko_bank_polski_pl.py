from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PkoBankPolskiPLSpider(Spider):
    name = "pko_bank_polski_pl"
    item_attributes = {"brand": "PKO BP", "brand_wikidata": "Q578832"}
    start_urls = ["https://www.pkobp.pl/api/modules/poi-map?top-left=54.776,14.064&bottom-right=48.934,24.932"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["unique_id"]
            if location["label"] == "atm_pko":
                apply_category(Categories.ATM, item)
                item["street_address"] = item.pop("addr_full", None)
                item["street_address"] = item.pop("addr_full", None)
                yield item
            elif location["label"] == "facility":
                apply_category(Categories.BANK, item)
                item["street_address"] = item.pop("addr_full", None)
                item["street_address"] = item.pop("addr_full", None)
                yield item
