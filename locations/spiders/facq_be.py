from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

STORES_QUERY = """
query Stores($locale: String!, $pagination: Store_Pagination) {
  Store_Stores(locale: $locale, pagination: $pagination) {
    items {
      storeName
      slug
      address
      postcode
      city
      latitude
      longitude
      storeUnits {
        internalRef
        storeUnitType {
          code
        }
        phone
        email
        openingHours {
          monday
          tuesday
          wednesday
          thursday
          friday
          saturday
        }
        services {
          code
        }
        overrideAddress
        overrideLatitude
        overrideLongitude
      }
    }
  }
}
"""

# A site hosts up to four kinds of outlet. Only the two that serve the public are collected:
# the "EXPOcenter" showrooms and the two Outlet Centers. The PROcenter trade counters and the
# regional warehouses sharing these addresses are for installers rather than for shoppers.
PUBLIC_UNIT_TYPES = ["showroom", "outletcenter"]

STORE_PATHS = {
    "fr": "fr/particuliers/magasins",
    "nl": "nl/particulieren/winkels",
    "en": "en/private-customers/stores",
}


class FacqBESpider(JSONBlobSpider):
    name = "facq_be"
    item_attributes = {"name": "Facq", "brand": "Facq", "brand_wikidata": "Q141496238"}
    allowed_domains = ["www.facq.be"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Only nl_BE, fr_FR and en_US are accepted; anything else fails validation server side.
        # French is the site's own default locale, and the only Belgian one whose addresses are
        # complete: the Dutch locale translates the street names of the bilingual Brussels sites
        # but leaves Wallonia in French, and the English locale simply repeats the French data.
        yield JsonRequest(
            url="https://www.facq.be/api/graphql",
            data={"query": STORES_QUERY, "variables": {"locale": "fr_FR", "pagination": {"limit": 500}}},
        )

    def extract_json(self, response: TextResponse) -> list[dict]:
        # Each outlet is a POI in its own right, with its own reference, contact details and
        # opening hours, so flatten them out and carry the shared site details down to each.
        units = []
        for store in response.json()["data"]["Store_Stores"]["items"]:
            site = {key: value for key, value in store.items() if key != "storeUnits"}
            for unit in store["storeUnits"]:
                if unit["storeUnitType"]["code"] in PUBLIC_UNIT_TYPES:
                    units.append(site | unit)
        return units

    def pre_process_data(self, feature: dict) -> None:
        # An outlet can sit at its own address, away from the rest of its site.
        address = feature.pop("address")
        feature["street_address"] = feature.pop("overrideAddress") or address
        feature["latitude"] = feature.pop("overrideLatitude") or feature["latitude"]
        feature["longitude"] = feature.pop("overrideLongitude") or feature["longitude"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["internalRef"]
        item["branch"] = item.pop("name").removeprefix("Facq ")

        unit_type = feature["storeUnitType"]["code"]
        for language, path in STORE_PATHS.items():
            url = f"https://www.facq.be/{path}/{feature['slug']}?storeUnit={unit_type}"
            item["extras"][f"website:{language}"] = url
        item["website"] = item["extras"]["website:fr"]

        item["opening_hours"] = self.parse_opening_hours(feature["openingHours"])

        apply_category(Categories.SHOP_BATHROOM_FURNISHING, item)

        services = [service["code"] for service in feature["services"]]
        apply_yes_no(Extras.DELIVERY, item, "delivery_anywhere_belgium" in services)

        yield item

    @staticmethod
    def parse_opening_hours(opening_hours: dict | None) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if times := (opening_hours or {}).get(day.lower()):
                open_time, close_time = (time.strip() for time in times.split("-"))
                oh.add_range(day, open_time, close_time)
        oh.set_closed("Su")
        return oh
