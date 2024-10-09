from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class AmpmUSSpider(Spider):
    name = "ampm_us"
    item_attributes = {"brand": "ampm", "brand_wikidata": "Q306960"}
    start_urls = ["https://www.ampm.com/handlers/getlocation.ashx?loc=45,-104&sl=true&isll=true&ns=1000000"]
    no_refs = True

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["state"] = location["state"]
            apply_yes_no(Extras.ATM, item, location["chaseATM"] != "")
            apply_yes_no(Extras.CAR_WASH, item, location["carwash"] == "TRUE")
            yield item
