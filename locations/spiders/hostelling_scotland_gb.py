
import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HostellingScotlandGBSpider(JSONBlobSpider):
    name = "hostelling_scotland_gb"
    start_urls = ["https://hostellingscotland.org.uk/our-hostels/search/"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        return json.loads(response.xpath('//script[@id="hostel-data"]/text()').get())

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["name"] = (feature.get("name") or "").strip() or None
        item["ref"] = feature["id"]

        # DictParser gives us these as-is, but they're site-relative paths.
        item["website"] = response.urljoin(feature["url"])
        if feature.get("imgPath"):
            item["image"] = response.urljoin(feature["imgPath"])

        if feature.get("area"):
            item["extras"]["area"] = feature["area"]
        if feature.get("text"):
            item["extras"]["description"] = feature["text"].strip()
        if feature.get("facilities"):
            item["extras"]["facilities"] = "; ".join(sorted(feature["facilities"]))

        if feature.get("isAffiliate"):
            # Independent hostel, only listed/bookable via Hostelling Scotland.
            item["operator"] = "Hostelling Scotland"
            item["operator_wikidata"] = "Q7438052"
            item["extras"]["affiliate"] = "yes"
        else:
            item["brand"] = "Hostelling Scotland"
            item["brand_wikidata"] = "Q7438052"

        apply_category(Categories.TOURISM_HOSTEL, item)

        yield item
