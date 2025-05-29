from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class ClarksSpider(JSONBlobSpider):
    name = "clarks"
    item_attributes = {"brand": "Clarks", "brand_wikidata": "Q1095857"}
    COUNTRY_MAPPINGS = {
        "GB": "UnitedKingdom",
        "US": "UnitedStates",
        "CA": "Canada",
        "IE": "Ireland",
    }
    locations_key = "hits"

    def start_requests(self):
        yield JsonRequest(
            url="https://kij46symwd-3.algolianet.com/1/indexes/prod_store/query?x-algolia-api-key=14be9e2da22ce62ef749138c685e623b&x-algolia-application-id=KIJ46SYMWD",
            data={"hitsPerPage": 1000},
        )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("_geoloc"))
        feature.update(feature.pop("address"))
        feature["street-address"] = merge_address_lines(
            [feature.pop("streetNumber", ""), feature.pop("streetName", "")]
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("objectID")
        country = self.COUNTRY_MAPPINGS.get(item["country"])
        store_locator = f'https://www.clarks.com/en-{item["country"].lower()}/store-locator'
        item["website"] = (
            f'{store_locator}/{country}/{item["city"]}/{item["ref"]}'.replace(" ", "") if country else store_locator
        )
        item["opening_hours"] = OpeningHours()
        for rule in feature.get("openingHours", []):
            if day := sanitise_day(rule.get("day")):
                if rule.get("openingTime") and rule.get("closingTime"):
                    item["opening_hours"].add_range(day, rule["openingTime"], rule["closingTime"])
        apply_category(Categories.SHOP_SHOES, item)
        yield item
