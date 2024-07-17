from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MazdaAUSpider(Spider):
    name = "mazda_au"
    item_attributes = {"brand": "Mazda", "brand_wikidata": "Q35996"}
    allowed_domains = ["www.mazda.com.au"]
    start_urls = ["https://www.mazda.com.au/api/dealers"]

    def parse(self, response):
        for location in response.json():
            for department in location["departments"]:
                item = DictParser.parse(location)
                item["ref"] = location["dealerCode"] + "_" + department["name"]
                item["street_address"] = item.pop("addr_full", None)
                item["phone"] = department["phone"]
                item["email"] = department["email"]
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(" ".join(department["hours"]))
                if department["name"] == "Sales":
                    apply_category(Categories.SHOP_CAR, item)
                elif department["name"] == "Parts":
                    apply_category(Categories.SHOP_CAR_PARTS, item)
                elif department["name"] == "Service":
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                else:
                    self.logger.error("Unknown department type ignored: {}".format(department["name"]))
                    continue
                yield item
