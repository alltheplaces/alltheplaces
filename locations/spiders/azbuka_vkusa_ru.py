from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AzbukaVkusaRUSpider(JSONBlobSpider):
    name = "azbuka_vkusa_ru"
    start_urls = ["https://services-api.av.ru/shops/byChannel/offline"]
    item_attributes = {
        "brand": "Азбука Вкуса",
        "brand_wikidata": "Q4058209",
    }
    locations_key = "data"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        # Name contains an address which is in address field;
        # also name_eng is available, but it's a bit inaccurate to capture
        item.pop("state")

        item["ref"] = feature.get("code")
        item["city"] = feature.get("region", {}).get("name")
        phone = feature.get("phone") or ""
        item["phone"] = "; ".join(phone.split(","))

        self.parse_hours(item, feature)
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_hours(self, item: Feature, feature: dict) -> None:
        for channel in feature.get("sale_channels", []):
            if channel.get("code") == "offline":
                try:
                    oh = OpeningHours()
                    for day, hours in channel.get("worktime", {}).items():
                        oh.add_range(day, hours.get("start"), hours.get("end"))

                    item["opening_hours"] = oh
                except Exception:
                    self.logger.exception("Error parsing hours for %s", item.get("ref"))
                    self.crawler.stats.inc_value("atp/hours/fail")
