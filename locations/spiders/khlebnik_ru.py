import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KhlebnikRUSpider(JSONBlobSpider):
    name = "khlebnik_ru"
    item_attributes = {
        "brand": "Хлебник",
        "brand_wikidata": "Q110085956",
    }
    start_urls = [
        "https://yandex.ru/map-widget/v1/api/slow/userMaps/getMap?ajax=1&csrfToken=eb353f6934fff81b73749302b523fff123eaf5ff%3A1777485745&s=60721504&sessionId=1777485744656456-4101773330445094890-balancer-l7leveler-kubr-yp-klg-218-BAL&um=constructor%3A5c8546cb1d289c8ccdd7172b5999f4a95a5c65e8fee6e847bf302fcd14150b31"
    ]
    locations_key = ["data", "features"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        title = feature.get("title", "")
        lines = [line.strip() for line in title.split("\n") if line.strip()]
        item["addr_full"] = lines[0] if lines else None
        item["ref"] = feature["zIndex"]
        item.pop("name", None)
        item["lon"] = feature["coordinates"][0]
        item["lat"] = feature["coordinates"][1]
        # TODO: this captures most of the hours, but needs some more work to get all of them
        if match := re.search(r"Режим работы\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", title):
            oh = OpeningHours()
            oh.add_ranges_from_string(f"Mo-Su {match.group(1)}-{match.group(2)}")
            item["opening_hours"] = oh
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
