from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LiquorCityZASpider(Spider):
    name = "liquor_city_za"
    item_attributes = {"brand": "Liquor City", "brand_wikidata": "Q116620538"}
    start_urls = [
        "https://lets-trade-client-prod.letstrade.global/v2/client/branches?client_id=689053976a0872f147baef68"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["content"]["branch_list"]:
            if not (address := location.pop("address", None)):
                continue
            location.update(address)
            item = DictParser.parse(location)
            if name := item.pop("name", None):
                item["branch"] = name.removeprefix("Liquor City ")
            item["ref"] = location["branch_number"]

            oh = OpeningHours()
            for day_time in location["working_hours"]:
                if "Public Holiday" in day_time["day"]:
                    continue
                if day_time.get("closed"):
                    oh.set_closed(day_time["day"])
                else:
                    oh.add_range(day=day_time["day"], open_time=day_time["from"], close_time=day_time["to"])
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
