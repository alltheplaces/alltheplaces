from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class MyerAUSpider(JSONBlobSpider):
    name = "myer_au"
    item_attributes = {"brand": "Myer", "brand_wikidata": "Q1110323"}
    start_urls = [
        "https://prod-api.aws.myer.com.au/v1/locations?locationType=PhysicalStore&locationStatus=OPEN&postcode=2000&radius=20000&resultsPerPage=100"
    ]
    locations_key = "locations"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.start_urls[0],
            headers={"x-api-key": "DFLMv0pRm5466wR3CS3TU5569wxjodwq2LCACqgX", "origin": "https://www.myer.com.au"},
        )

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("locationId")
        address = location.pop("address")
        location["street_address"] = merge_address_lines([address.get(f"addressLine{i}") for i in range(1, 7)])
        location["phone"] = location.pop("contactInformation").get("dayPhone")
        location.update(location.pop("coordinates"))

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = location["longName"]
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
