from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class EssexUSSpider(JSONBlobSpider, PlaywrightSpider):
    name = "essex_us"
    start_urls = ["https://www.essexapartmenthomes.com/api/properties/search?query="]
    item_attributes = {
        "operator": "Essex",
        "operator_wikidata": "Q134703255",
    }
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    requires_proxy = True

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        return response.json()["communities"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["image"] = feature["imagelist"].split("|")[0]
        item["street_address"] = item.pop("addr_full")
        item["lat"], item["lon"] = feature["coordinate"].split(",")
        item["website"] = response.urljoin(feature["communityurl"])
        amenities = feature["communityamenities"]
        apply_yes_no(Extras.PETS_ALLOWED, item, "Pet friendly" in amenities)
        apply_yes_no(Extras.SWIMMING_POOL, item, "Swimming pool" in amenities)

        apply_category(Categories.RESIDENTIAL_APARTMENTS, item)

        yield item
