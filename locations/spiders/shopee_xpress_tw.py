import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

SHOPEE_XPRESS = {"brand_wikidata": "Q109676747"}
SIMPLE_MART = {"brand_wikidata": "Q15914017"}


class ShopeeXpressTWSpider(Spider):
    name = "shopee_xpress_tw"
    start_urls = [
        "https://spx.tw/api/service-point/point/around/list?radius=400000000&latitude=25.740539&longitude=121.8713269",
        "https://spx.tw/api/service-point/point/around/list?radius=400000000&latitude=21.749306&longitude=120.7836804",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["list"]:
            item = DictParser.parse(location)
            item["name"] = location["alias"]
            item["website"] = "https://spx.tw/service-point/detail/{}".format(item["ref"])

            if location["sp_point_type"] == 1:
                item.update(SHOPEE_XPRESS)
                # Some are "parcel lockers"
                # others have staff and some ability to buy some things off the shelf
                # TODO

                for k, v in location.items():
                    if v:
                        item["extras"]["x_{}".format(k)] = str(v)
            elif location["sp_point_type"] == 2:
                item["name"] = None
                item.update(SIMPLE_MART)
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = "SPX Express"
            else:
                self.logger.error("Unexpected type: {}".format(location["sp_point_type"]))

            try:
                if hours := location["open_hours"]:
                    item["opening_hours"] = self.parse_opening_hours(json.loads(hours))
            except:
                self.logger.error("Error parsing opening hours")

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            oh.add_days_range(rule["day"], rule["hours"][0], rule["hours"][1])
        return oh
