from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TvoeRUSpider(JSONBlobSpider):
    name = "tvoe_ru"
    item_attributes = {"brand": "ТВОЕ", "brand_wikidata": "Q110034939"}
    start_urls = ["https://tvoe.ru/api/shops/"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item["street_address"] = item.pop("addr_full")
        oh = OpeningHours()
        open_time, close_time = feature["workhours"].replace(" ", "").split("-")
        oh.add_days_range(DAYS, open_time, close_time)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
