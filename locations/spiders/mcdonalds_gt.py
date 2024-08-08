import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsGTSpider(scrapy.Spider):
    name = "mcdonalds_gt"
    item_attributes = McdonaldsSpider.item_attributes
    acustom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://mcdonalds.com.gt/restaurantes"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath("//@data-page").get())
        for location in data["props"]["restaurants"]:
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["name"]
            item["addr_full"] = location["address"]
            item["email"] = location["email"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["categorias"])

            for oh_rules in (
                location["horarios"].values() if isinstance(location["horarios"], dict) else location["horarios"]
            ):
                if oh_rules["name"] == "Restaurante":
                    item["opening_hours"] = OpeningHours()
                    for rule in oh_rules["horarios"]:
                        if day := sanitise_day(rule["description"], DAYS_ES):
                            item["opening_hours"].add_range(day, rule["start_time"], rule["end_time"])

            yield item
