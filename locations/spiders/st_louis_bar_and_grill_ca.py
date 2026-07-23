import json
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class StLouisBarAndGrillCASpider(JSONBlobSpider):
    name = "st_louis_bar_and_grill_ca"
    item_attributes = {"brand": "St. Louis Bar & Grill", "brand_wikidata": "Q65567668"}
    start_urls = ["https://locations.stlouiswings.com/"]

    def extract_json(self, response: Response) -> list[dict]:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        return data["props"]["pageProps"]["locations"]

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("storeCode")
        location["postcode"] = location.pop("postalCode", None)
        location["street_address"] = ", ".join(location.get("addressLines") or [])
        location["phone"] = (location.get("phoneNumbers") or [None])[0]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("website", None)
        item.pop("name", None)

        item["opening_hours"] = OpeningHours()
        for day, hours in zip(DAYS, location.get("businessHours") or []):
            if not hours or None in hours:
                continue
            open_time, close_time = hours
            item["opening_hours"].add_range(day, open_time, "24:00" if close_time == "00:00" else close_time)

        apply_category(Categories.RESTAURANT, item)
        yield item
