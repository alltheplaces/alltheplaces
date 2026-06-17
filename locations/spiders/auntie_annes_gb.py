import re
from typing import Iterable

import chompjs
from scrapy.http import Response, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AuntieAnnesGBSpider(JSONBlobSpider):
    name = "auntie_annes_gb"
    item_attributes = {"brand": "Auntie Anne's", "brand_wikidata": "Q4822010"}
    start_urls = ["https://www.auntieannes.co.uk/locations/"]
    drop_attributes = {"facebook", "twitter"}

    def extract_json(self, response: Response) -> dict | list[dict]:
        return chompjs.parse_js_object(
            re.search(
                r'"objects":(\[.+?]),"schema"',
                response.xpath("//script[contains(text(), 'mapsvg_options')]/text()").get(),
            ).group(1)
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not isinstance(feature.get("location"), dict):
            return
        address = feature["location"]["address"]
        item["addr_full"] = address["formatted"]
        item["city"] = address.get("postal_town") or address.get("locality")
        item["lat"], item["lon"] = feature["location"]["geoPoint"]["lat"], feature["location"]["geoPoint"]["lng"]
        item["branch"] = item.pop("name")
        item["country"] = address["country"]
        item["opening_hours"] = OpeningHours()
        time = re.sub("<[^<]+?>", "", str(feature.get("opening_hours") or ""))
        item["opening_hours"].add_ranges_from_string(time)
        if store_image := feature.get("store_image"):
            item["image"] = response.urljoin(store_image[0]["full"])
        apply_yes_no(Extras.DELIVERY, item, feature.get("delivery_available"))
        apply_yes_no(Extras.INDOOR_SEATING, item, feature.get("dinein_available"))
        apply_category(Categories.FAST_FOOD, item)
        yield item
