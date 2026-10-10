import re
from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class BakersDelightAUSpider(JSONBlobSpider):
    name = "bakers_delight_au"
    item_attributes = {"brand": "Bakers Delight", "brand_wikidata": "Q4849261"}
    locations_key = "locations"

    async def start(self) -> AsyncIterator[Request]:
        # The store locator page references a versioned, theme-asset-hosted
        # JSON file with the full list of bakeries. The theme asset path
        # (and cache-busting query string) can change on redeploy, so it is
        # discovered from the page rather than hard coded.
        yield Request("https://www.bakersdelight.com.au/pages/store-locator", callback=self.parse_store_locator_page)

    def parse_store_locator_page(self, response: TextResponse):
        if json_url := response.css("[data-locations-json-url]::attr(data-locations-json-url)").get():
            yield response.follow(json_url, callback=self.parse)

    def pre_process_data(self, feature: dict) -> None:
        address = feature.get("address") or {}
        feature["street_address"] = clean_address([address.get("address1"), address.get("address2")])
        feature["phone"] = address.get("phone")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"].rsplit("/", 1)[-1]
        item["branch"] = item.pop("name", "").removesuffix(" Bakery")
        item["state"] = feature.get("address", {}).get("provinceCode") or item.get("state")

        slug = re.sub(r"[^a-z0-9]+", "-", item["branch"].lower()).strip("-") + "-bakery"
        item["website"] = f"https://www.bakersdelight.com.au/pages/bakeries/{slug}"

        if hours := feature.get("metafields", {}).get("openingHours"):
            item["opening_hours"] = OpeningHours()
            for day, day_hours in hours.items():
                item["opening_hours"].add_range(day, day_hours.get("open"), day_hours.get("close"))

        apply_category(Categories.SHOP_BAKERY, item)
        yield item
