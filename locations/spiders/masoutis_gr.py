from typing import Any

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class MasoutisGRSpider(Spider):
    name = "masoutis_gr"
    item_attributes = {"brand_wikidata": "Q6783887"}
    allowed_domains = ["www.masoutis.gr"]

    def start_requests(self):
        yield FormRequest(
            url="https://www.masoutis.gr/api/masoutis/GetAllStoresEnabledLinks", method="POST", formdata={}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["Storeid"]
            item["image"] = location["PhotoData"]
            item["lat"] = location["Langitude"]
            item["lon"] = location["Longitude"]

            if location["KategoryIDEn"] == "CASH & CARRY":
                apply_category(Categories.SHOP_WHOLESALE, item)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)

            apply_yes_no(Extras.ATM, item, location["IfAtm"])
            apply_yes_no("fuel", item, location["IFGasStation"])
            apply_yes_no("butcher", item, location["IFbutchershop"])
            apply_yes_no("grocer", item, location["IFgroceryShop"])
            apply_yes_no("bakery", item, location["IfBakery"])
            apply_yes_no("fish", item, location["IfFishShop"])
            apply_yes_no("childcare", item, location["IfChildCare"])
            apply_yes_no("cafe", item, location["IfCafe"])

            yield item
