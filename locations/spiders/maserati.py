from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MaseratiSpider(scrapy.Spider):
    name = "maserati"
    item_attributes = {
        "brand": "Maserati",
        "brand_wikidata": "Q35962",
    }
    allowed_domains = ["maserati.com"]
    start_urls = [
        "https://api.onthemap.io/server/v1/api/location?language=en&sort=dealername&key=6e0b94fb-7f95-11ec-9c36-eb25f50f4870&channel=www.maserati.com",
    ]

    def parse(self, response: Response, **kwargs) -> Any:
        for row in response.json().get("data", {}).get("results", {}).get("features"):
            row.update(row.pop("properties"))
            item = DictParser.parse(row)
            item["ref"] = row.get("otm_id")
            item["street_address"] = item.pop("addr_full")
            item["country"] = row["countryIsoCode2"]
            item["email"] = row["emailAddr"]
            item["name"] = row["dealername"]

            is_service = row.get("assistance") == "true" or row.get("autoBodyShop") == "true"

            if row.get("sales") == "true":
                sales_item = item.deepcopy()
                sales_item["ref"] = f"{item['ref']}-sales"
                apply_category(Categories.SHOP_CAR, sales_item)
                apply_yes_no(Extras.CAR_REPAIR, sales_item, is_service)
                self.parse_hours(sales_item, row.get("opening_hours", []))
                yield sales_item

            if is_service:
                service_item = item.deepcopy()
                service_item["ref"] = f"{item['ref']}-service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                apply_yes_no(Extras.BODY_REPAIR, service_item, row.get("autoBodyShop") == "true")
                self.parse_hours(service_item, row.get("service_opening_hours", []))
                yield service_item

    def parse_hours(self, item: Feature, hours: list) -> None:
        try:
            if not hours:
                return
            oh = OpeningHours()
            for day_info in hours:
                oh.add_range(DAYS[int(day_info["day"]) - 1], day_info["amFrom"], day_info["amTo"])
                oh.add_range(DAYS[int(day_info["day"]) - 1], day_info.get("pmFrom"), day_info.get("pmTo"))
            item["opening_hours"] = oh
        except Exception as e:
            self.logger.error(f"Error parsing hours {hours} for {item['ref']}: {e}")
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/fail")
