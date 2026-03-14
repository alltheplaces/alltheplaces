from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class AlainAfflelou2Spider(Spider):
    name = "alain_afflelou2"
    item_attributes = {"brand": "Alain Afflelou", "brand_wikidata": "Q2829511"}
    start_urls = [
        "https://www.afflelou.ch/afflelou_storelocator/location/getlist/",
        "https://www.afflelou.pt/afflelou_storelocator/location/getlist/",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for base_location in response.json()["data"]["items"].values():
            if len(base_location["locations"]) == 1:
                location_info = base_location | base_location["locations"][0]
                item = DictParser.parse(location_info)
                if location_info.get("is_audio"):
                    apply_category(Categories.SHOP_HEARING_AIDS, item)
                else:
                    apply_category(Categories.SHOP_OPTICIAN, item)
            else:  # optician with hearing aid facility
                for sub_location in base_location["locations"]:
                    if not sub_location.get("is_audio"):  # optician
                        location_info = base_location | sub_location
                        break
                item = DictParser.parse(location_info)
                apply_category(Categories.SHOP_OPTICIAN, item)
                apply_yes_no("hearing_aids", item, True)

            item.pop("name")
            item["street_address"] = item.pop("addr_full", None)
            yield item
