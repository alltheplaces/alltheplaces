from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class ColumbusCafeFRSpider(JSONBlobSpider):
    name = "columbuscafe_fr"
    item_attributes = {"brand": "Columbus Café & Co", "brand_wikidata": "Q2984582"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.columbuscafe.com/wp/wp-admin/admin-ajax.php?action=storelocator"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("content"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature.get("address") in ["false", False]:
            item["name"] = None
            item["ref"] = feature.get("ID")
            address = clean_address(feature.get("address")).split("Tél :")
            item["addr_full"] = address[0]
            item["phone"] = ";".join(address[1:]).replace(",", "").strip()

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FR:
                if day_data := feature.get(day.lower()):
                    time = day_data.replace("de", "").replace("h", ":").strip()
                    if time in ["Fermé", None]:
                        continue
                    open_time, close_time = time.split(" à ")
                    day = sanitise_day(day, DAYS_FR)
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip())

            item["website"] = feature["link"]
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
