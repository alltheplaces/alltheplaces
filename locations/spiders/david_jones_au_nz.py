import re
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class DavidJonesAUNZSpider(JSONBlobSpider):
    name = "david_jones_au_nz"
    item_attributes = {"brand": "David Jones", "brand_wikidata": "Q5235753"}
    allowed_domains = ["www.davidjones.com"]
    start_urls = ["https://www.davidjones.com/stores"]
    requires_proxy = True

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        js_blob = response.xpath('//script[contains(text(), "window.geodata = ")]/text()').get()
        js_blob = re.sub(r"\s+", " ", js_blob)
        js_blob = js_blob.split("stores: ", 1)[1].split("} // ]]", 1)[0]
        json_data = parse_js_object(js_blob)
        return json_data

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("street", None)
        item["street_address"] = merge_address_lines([feature.get("street"), feature.get("suburb")])
        item["city"] = feature.get("city")
        slug = feature.get("url")
        item["website"] = f"https://www.davidjones.com{slug}"
        item.pop("phone", None)  # Not unique to each store
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
