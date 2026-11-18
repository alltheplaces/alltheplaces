from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines

PEPE_JEANS = {"brand": "Pepe Jeans", "brand_wikidata": "Q426992"}


class PepeJeansSpider(Spider):
    name = "pepe_jeans"

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.pepejeans.com/mobify/slas/private/shopper/auth/v1/organizations/f_ecom_blrq_prd/oauth2/token",
            formdata={"grant_type": "client_credentials", "channel_id": "PJG-ES"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = response.json()["access_token"]
        yield JsonRequest(
            url="https://www.pepejeans.com/mobify/proxy/api/store/shopper-stores/v1/organizations/f_ecom_blrq_prd/store-search?distanceUnit=km&latitude=0&longitude=0&maxDistance=20000&siteId=PJG-ES&limit=200",
            headers={"Authorization": f"Bearer {token}"},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location["street_address"] = merge_address_lines(
                [location.pop("address1", None), location.pop("address2", None)]
            )
            item = DictParser.parse(location)
            item.pop("phone", None)
            item.pop("email", None)
            item.pop("state", None)

            name = location["name"]
            if name.startswith("AWWG Outlet "):
                item["name"] = "AWWG Outlet"
                item["branch"] = name.removeprefix("AWWG Outlet ")
            elif name.startswith("Pepe Jeans "):
                item.update(PEPE_JEANS)
                branch = name.removeprefix("Pepe Jeans ")
                if location.get("c_StoreType") == "Outlet":
                    item["name"] = "Pepe Jeans Outlet"
                    branch = branch.removeprefix("Outlet Factory ").removeprefix("Outlet ").removesuffix(" Outlet")
                else:
                    item["name"] = "Pepe Jeans"
                item["branch"] = branch

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
