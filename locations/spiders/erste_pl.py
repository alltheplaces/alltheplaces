import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.central_england_cooperative import set_operator


class ErstePLSpider(Spider):
    name = "erste_pl"
    item_attributes = {"brand": "Erste", "brand_wikidata": "Q806653"}
    start_urls = ["https://www.erste.pl/_js_places/places.js"]

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(response.text)
        for ref, branch in data["atm"].items():
            yield self.parse_item(ref, branch, Categories.ATM)
        for ref, branch in data["branch"].items():
            yield self.parse_item(ref, branch, Categories.BANK)
        for ref, branch in data["cashin"].items():
            item = self.parse_item(ref, branch, Categories.ATM)
            apply_yes_no("cash_in", item, True)
            yield item

    @staticmethod
    def parse_item(ref: str, data: dict, category) -> Feature:
        data["basicParameters"]["street_address"] = data["basicParameters"].pop("street")
        item = DictParser.parse(data["basicParameters"])
        item["ref"] = ref

        if data["open_24h"]:
            item["opening_hours"] = "24/7"
        else:
            item["opening_hours"] = OpeningHours()
            for day, hours in data["basicParameters"]["opening_hours"].items():
                start_time, end_time = hours.split("-")
                item["opening_hours"].add_range(DAYS[int(day) - 2], start_time.strip(), end_time.strip())

        if category == Categories.ATM:
            item["name"] = None
            set_operator(ErstePLSpider.item_attributes, item)
        else:
            item["branch"] = item.pop("name")

        apply_category(category, item)

        return item
