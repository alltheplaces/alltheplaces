import json
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BootsGBSpider(JSONBlobSpider):
    name = "boots_gb"
    item_attributes = {"brand": "Boots", "brand_wikidata": "Q6123139"}
    locations_key = "searchResults"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("GB", 100000):
            yield JsonRequest(
                url=f'https://www.boots.com/AjaxStoreLocatorSearch?storeId=11352&storeAddressSearch_city={city["name"]}&requesttype=ajax',
                method="GET",
            )

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        data = response.text.replace("/*", "").replace("*/", "")
        json_data = json.loads(data)
        if not "errorMessageKey" in json_data:
            if self.locations_key:
                if isinstance(self.locations_key, str):
                    json_data = json_data[self.locations_key]
                elif isinstance(self.locations_key, list):
                    for key in self.locations_key:
                        json_data = json_data[key]
            return json.loads(json_data)

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("storeId"):
            feature["ref"] = feature["storeId"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not item.get("ref"):
            return
        if item["name"].startswith("Opticians"):
            item["brand"] = "Boots Opticians"
            item["brand_wikidata"] = "Q4944037"
            item["name"] = item["name"].replace("Opticians", "").strip("- ")
            apply_category(Categories.SHOP_OPTICIAN, item)
        else:
            apply_category(Categories.PHARMACY, item)
        item["branch"] = item.pop("name")
        item["postcode"] = feature["storeAddPostcode"]
        item["city"] = feature["storeAddCity"]
        item["state"] = feature["storeAddCounty"]
        item["street_address"] = merge_address_lines(
            [feature["storeAddL1"], feature["storeAddL2"], feature["storeAddL3"]]
        )
        yield item
