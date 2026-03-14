from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FutonCompanyGBSpider(JSONBlobSpider):
    name = "futon_company_gb"
    item_attributes = {"brand": "Futon Company", "brand_wikidata": "Q117382562"}
    start_urls = ["https://www.futoncompany.co.uk/store-locator.html"]
    nsi_id = "N/A"

    def extract_json(self, response: Response) -> list[dict]:
        script = response.xpath('//script[contains(text(), "storeData")]/text()').get()
        start = script.index("storeData")
        return chompjs.parse_js_object(script[start:])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("store_location_id")
        name = item.pop("name")
        item["branch"] = name.removesuffix(" Shop")
        item["website"] = "https://www.futoncompany.co.uk/" + name.lower().replace(" ", "-") + ".html"
        item["addr_full"] = feature.get("pickup_address")
        item["phone"] = feature.get("pickup_phone")
        item["email"] = feature.get("pickup_email")

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature["pickup_time"])

        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
