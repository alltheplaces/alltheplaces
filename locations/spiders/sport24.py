from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Sport24Spider(JSONBlobSpider):
    name = "sport24"
    item_attributes = {"brand": "Sport 24", "brand_wikidata": "Q121503172"}
    start_urls = ["https://www.sport24.dk/stores/"]
    skip_auto_cc_domain = True

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"][
            "pageProps"
        ]["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["navLocationCode"]
        item["website"] = response.urljoin(f'{feature["link"].strip()}/')
        item["lat"], item["lon"] = feature["locationCoordinates"].split(",")
        item["branch"] = item.pop("name")
        item["name"] = feature.get("type")
        item["street_address"] = item.pop("street")
        if opening_hours := feature.get("openingHours"):
            item["opening_hours"] = OpeningHours()
            for rule in opening_hours:
                if rule["openTime"].get("hours") and rule["closeTime"].get("hours"):
                    open_time, close_time = [
                        f"{hour}:00" for hour in [str(rule["openTime"]["hours"]), str(rule["closeTime"]["hours"])]
                    ]
                    item["opening_hours"].add_range(rule["openDay"], open_time, close_time)

        apply_category(Categories.SHOP_SPORTS, item)
        yield item
