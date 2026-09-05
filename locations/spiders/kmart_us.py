from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import postal_regions
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

KMART_SHARED_ATTRIBUTES = {
    "brand": "Kmart",
    "brand_wikidata": "Q1753080",
}


class KmartUSSpider(JSONBlobSpider):
    name = "kmart_us"
    item_attributes = KMART_SHARED_ATTRIBUTES
    allowed_domains = ["www.kmart.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Kmart has shrunk to a tiny handful of stores remaining in US
        # territories (Guam, US Virgin Islands) with no stores left in
        # the continental US. There is no sitemap or bulk store list, so
        # a postcode radius search (max radius 300 miles) is used, as
        # suggested in https://github.com/alltheplaces/alltheplaces/issues/764.
        # A min_population filter of 50000 keeps the request count down
        # for the continental US (where no stores remain in any case)
        # while still covering all postcodes in Guam/Puerto Rico/US
        # Virgin Islands/Northern Mariana Islands/American Samoa, since
        # those postcodes have no population figure in the source data
        # and therefore always pass the filter.
        for postal_region in postal_regions("US", min_population=50000, consolidate_cities=True):
            yield JsonRequest(
                url="https://www.kmart.com/api/sal/v1/store/stores?store=Kmart&mileRadius=300&caller=storeLocator"
                "&includeFilterStrTypes=002_A%7C002_B%7C001_O%7C001_A%7C001_B%7C001_C%7C001_D"
                f"&zipCode={postal_region['postal_region']}",
                headers={"Authorization": "KMART"},
            )

    def extract_json(self, response: Response) -> list[dict]:
        return response.json().get("stores", [])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("isActive") != "1":
            return

        item["ref"] = feature.get("storeNumber")
        item["state"] = feature["address"].get("stateCode")
        if contact_numbers := feature["address"].get("contactNumbers"):
            item["phone"] = contact_numbers[0]

        item["opening_hours"] = OpeningHours()
        for day, hours in feature.get("hours", {}).items():
            if (day_name := DAYS_EN.get(day.title())) is None:
                continue
            open_hour, open_minute = divmod(int(hours["openTime"]) // 60, 60)
            close_hour, close_minute = divmod(int(hours["closeTime"]) // 60, 60)
            item["opening_hours"].add_range(
                day_name, f"{open_hour:02d}:{open_minute:02d}", f"{close_hour:02d}:{close_minute:02d}"
            )

        if not item["opening_hours"]:
            # A handful of non-store entries are returned by the API,
            # such as Kmart's former corporate headquarters address in
            # Hoffman Estates, IL, which has no opening hours on any
            # day of the week. These are not real, publicly accessible
            # stores and are excluded.
            return

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

        yield item
