from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class LamaisonFRSpider(JSONBlobSpider):
    name = "lamaison_fr"
    item_attributes = {"brand": "LaMaison.fr", "brand_wikidata": "Q127596118", "name": "LaMaison.fr"}
    allowed_domains = ["www.lamaison.fr"]
    start_urls = ["https://www.lamaison.fr/stores"]
    name_is_branch = True

    def extract_json(self, response: TextResponse) -> list[dict]:
        markers = chompjs.parse_js_object(response.text.split('"markers":', 1)[1])
        # The store locator also lists Agrial-branded stores.
        return [marker for marker in markers if marker.get("signName") == "LaMaison.fr"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines(feature.get("address") or [])
        item["email"] = feature.get("contact_mail")

        week = (feature.get("schedule") or {}).get("openingHours") or []
        if any(week):
            item["opening_hours"] = OpeningHours()
            for day, slots in zip(DAYS_FROM_SUNDAY, week):
                if not slots:
                    item["opening_hours"].set_closed(day)
                else:
                    for slot in slots:
                        item["opening_hours"].add_range(day, slot.get("start_time"), slot.get("end_time"))

        apply_category(Categories.SHOP_GARDEN_CENTRE, item)
        yield item
