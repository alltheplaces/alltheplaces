from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mitsubishi import MitsubishiSpider


class MitsubishiGBSpider(Spider):
    name = "mitsubishi_gb"
    item_attributes = MitsubishiSpider.item_attributes
    start_urls = ["https://mitsubishi-motors.co.uk/find-a-dealer/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.dealers")]/text()').get()
        ):
            if location["active"] is not True:
                continue

            item = DictParser.parse(location["basic"])
            item["name"] = location["basic"]["listname"]
            item["extras"]["ref:vatin"] = location["basic"]["vatnumber"]
            item["ref"] = location["did"]
            item["street_address"] = merge_address_lines(
                [
                    location["addresses"]["visiting_address"]["street_1"],
                    location["addresses"]["visiting_address"]["street_2"],
                    location["addresses"]["visiting_address"]["street_3"],
                ]
            )
            item["postcode"] = location["addresses"]["visiting_address"]["postalcode"]
            item["lat"] = location["addresses"]["visiting_address"]["lat"]
            item["lon"] = location["addresses"]["visiting_address"]["long"]

            for t, c in [
                ("showroom", Categories.SHOP_CAR),
                ("parts", Categories.SHOP_CAR_PARTS),
                ("workshop", Categories.SHOP_CAR_REPAIR),
            ]:
                if hours := location["openinghours"].get(t):
                    dep = item.deepcopy()
                    dep["ref"] = "{}_{}".format(item["ref"], t)
                    dep["opening_hours"] = self.parse_opening_hours(hours)

                    apply_category(c, dep)

                    yield dep

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            if ":" in rules[day]["open"]:
                oh.add_range(day, rules[day]["open"], rules[day]["close"])
        return oh
