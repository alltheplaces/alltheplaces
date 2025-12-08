import re
from typing import Any

import chompjs
from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_BG, DAYS_EN, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBGSpider(Spider):
    name = "mcdonalds_bg"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.bg"]
    start_urls = ["https://mcdonalds.bg/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        ajax_endpoints = chompjs.parse_js_object(response.xpath('//script[@id="wgs-endpoints-js-extra"]/text()').get())
        ajax_action = "get_filtered_posts"
        yield FormRequest(
            url="https://mcdonalds.bg/wp-admin/admin-ajax.php",
            formdata={"action": ajax_action, "ajax-nonce": ajax_endpoints["nonce"][ajax_action]},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["city"] = location.get("city", {}).get("city_name")
            if phone_numbers := location.get("phone_numbers", []):
                item["phone"] = phone_numbers[0]

            for benefit in location.get("benefits", []):
                apply_yes_no(Extras.WIFI, item, benefit.get("name") == "WiFi")
                apply_yes_no(Extras.DRIVE_THROUGH, item, benefit.get("name") == "McDrive™")

            apply_yes_no(Extras.DELIVERY, item, location.get("is_delivery_available"))

            item["opening_hours"] = self.parse_opening_hours(location.get("business_hours", []))

            if work_hours := location.get("work_hours", []):
                for work_hour in work_hours:
                    if work_hour.get("label") == "McDrive™":
                        oh = OpeningHours()
                        oh.add_days_range(DAYS, work_hour.get("opens_at"), work_hour.get("closes_at"))
                        item["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()
                        break

            yield item

    def parse_opening_hours(self, opening_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            if not rule.get("label") or "Ресторант" in rule.get("label"):
                days_format = DAYS_EN
                days = "Mo-Su"
            elif re.search(r"[a-zA-Z]+", rule.get("label")):
                days_format = DAYS_EN
                days = rule.get("label")
            else:
                days_format = DAYS_BG
                days = rule.get("label")
            oh.add_ranges_from_string(f'{days}: {rule.get("opens_at")} to {rule.get("closes_at")}', days=days_format)
        return oh
