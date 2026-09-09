import json
import re

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class BexleySpider(JSONBlobSpider):
    name = "bexley"
    item_attributes = {
        "brand": "Bexley",
        "brand_wikidata": "Q101247434",
    }
    # the start page must be any shop url
    start_urls = ["https://www.bexley.fr/boutiques/bexley-creteil-soleil"]

    def extract_json(self, response):
        script = response.xpath("//script[contains(., 'soonStoreLocator')]/text()").get()

        match = re.search(r'"items"\s*:\s*', script)
        if not match:
            raise ValueError("items not found")

        # Position immediately after: "items":
        start = match.end()
        decoder = json.JSONDecoder()
        items, end = decoder.raw_decode(script[start:])
        return items

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_SHOES, item)

        item["country"] = location.get("country_id") or ""

        url_key = location.get("url_key")
        if url_key is not None:
            item["website"] = "https://www.bexley.fr/boutiques/" + url_key
        item["branch"] = item.pop("name", "").removeprefix("BEXLEY ")
        yield item
