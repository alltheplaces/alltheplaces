from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ArmaguardAUSpider(scrapy.Spider):
    name = "armaguard_au"
    item_attributes = {"brand": "Armaguard", "brand_wikidata": "Q118898974"}
    start_urls = [
        "https://app.ehoundplatform.com/api/1.3/proximity_search?output=json&lat=-33.867139&lon=151.207114&count=5000&priority_distance=undefined&priority_filters=undefined&priority_logic=undefined&log_type=web&create_log=true&api_key=a34dcb3a0c98793&custom_logic=undefined&user_selection=undefined&ch=7203"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for atm in response.json()["record_set"]:
            item = DictParser.parse(atm)
            item["ref"] = atm["loc_id"]
            item["branch"] = atm["details"]["location_name"]
            item["opening_hours"] = OpeningHours()
            if atm["opening_hours"]["abbr_opening_hours"] == "open 24x7":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"].add_ranges_from_string(atm["opening_hours"]["abbr_opening_hours"])
            yield item
