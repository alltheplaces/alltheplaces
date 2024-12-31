from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class IonitySpider(Spider):
    name = "ionity"
    item_attributes = {"brand": "Ionity", "brand_wikidata": "Q42717773"}

    # Ionity API found from its payment website: https://payment.ionity.eu/dashboard

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://ionity-api.ionity.cloud/api/v1/user/collective")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://ionity-api.ionity.cloud/api/v2/charging-point",
            headers={"Authorization": f'Bearer {response.json()["accessToken"]}'},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            apply_category(Categories.CHARGING_STATION, item)
            yield item
