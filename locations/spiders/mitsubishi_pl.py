import re
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiPLSpider(JSONBlobSpider):
    name = "mitsubishi_pl"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi.pl/dealerzy"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            re.search(
                r"dealerLocations\":(\[.*\])}\]\],\[\[\"\$\"",
                response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
            ).group(1)
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["addr_full"] = feature["full_address"]
        item["name"] = feature["dealer_name"]

        services = feature["services"]
        if "SHOWROOM" in services:
            apply_category(Categories.SHOP_CAR, item)
            if "SERVICE" in services:
                apply_yes_no(Extras.CAR_REPAIR, item, True)
        elif "SERVICE" in services:
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        if isinstance(feature["dealer_websites"], list):
            item["website"] = feature["dealer_websites"][0]["url"]

        yield item
