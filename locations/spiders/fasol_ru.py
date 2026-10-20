from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FasolRUSpider(JSONBlobSpider):
    name = "fasol_ru"
    item_attributes = {"brand": "Фасоль", "brand_wikidata": "Q132005368"}
    start_urls = ["https://api.metro-cc.ru/api/v1/C98BB1B547ECCC17D8AEBEC7116D6/fasol/stores"]
    locations_key = "data"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item.pop("name")
        item["addr_full"] = location["address"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(DAYS, *location["work_mode"].split("-"))
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
