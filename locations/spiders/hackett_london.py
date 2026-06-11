from typing import Any, AsyncIterator

from scrapy.http import FormRequest, JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class HackettLondonSpider(Spider):
    name = "hackett_london"
    item_attributes = {"brand": "Hackett London", "brand_wikidata": "Q1136426"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.hackett.com/mobify/slas/private/shopper/auth/v1/organizations/f_ecom_blrq_prd/oauth2/token",
            formdata={
                "grant_type": "refresh_token",
                "refresh_token": "cZ5zAoHyxVCwqOccdo2EPeVG8sP8OWRiiMlx9DqrHhQ",  # refresh token (valid ~30 days), couldn't find a way to generate it dynamically.
                "channel_id": "HKT-ES",
                "dnt": "false",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = response.json()["access_token"]
        yield JsonRequest(
            url="https://www.hackett.com/mobify/proxy/api/store/shopper-stores/v1/organizations/f_ecom_blrq_prd/store-search?distanceUnit=km&latitude=0&longitude=0&maxDistance=20000&siteId=HKT-ES&limit=200",
            headers={"Authorization": f"Bearer {token}"},
            callback=self.parse_location,
        )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location["address"] = merge_address_lines([location.pop("address1", None), location.pop("address2", None)])
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Hackett ").removeprefix("Outlet ")
            if "Outlet" in location["name"]:
                item["name"] = "Hackett London Outlet"
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
