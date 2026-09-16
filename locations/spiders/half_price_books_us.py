from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class HalfPriceBooksUSSpider(JSONBlobSpider):
    name = "half_price_books_us"
    item_attributes = {"brand": "Half Price Books", "brand_wikidata": "Q5641744"}
    locations_key = "stores"
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.hpb.com/on/demandware.store/Sites-hpb-Site/en_US/Stores-FindStores?fromStoreFinder=true&radius=3000&lat=39.0997&long=-94.5786",
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").removeprefix("HPB ")
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        item["website"] = f'https://www.hpb.com/store?storeid={feature["ID"]}'
        if store_hours := feature.get("storeHours"):
            item["opening_hours"] = self.parse_opening_hours(store_hours)
        apply_category(Categories.SHOP_BOOKS, item)
        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hours in rules.items():
            opening_hours.add_ranges_from_string(f'{day} {hours["open"]} - {hours["close"]}')
        return opening_hours
