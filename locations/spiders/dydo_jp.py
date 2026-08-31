from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature

GRAPHQL_QUERY = """
query SearchVendingMachines($lon: numeric!, $lat: numeric!, $radius: Int!) {
    search_vending_machines(args: {
        p_longitude: $lon
        p_latitude: $lat
        p_max: $radius
    }) {
        vending_machine_id
        longitude
        latitude
        prefecture
        city
        address
        base
        inner
        vending_machine_type1
        product_name1
        product_name2
    }
}"""


class DydoJPSpider(Spider):
    name = "dydo_jp"
    item_attributes = {"brand": "ダイドー", "brand_wikidata": "Q11316814"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lt, ln in country_iseadgg_centroids("JP", 24):
            yield JsonRequest(
                url="https://vending-api.dydo.cmsod.jp/v1/graphql",
                data={
                    "query": GRAPHQL_QUERY,
                    "variables": {"lon": ln, "lat": lt, "radius": 24000},
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["search_vending_machines"]:

            item = Feature()

            item["ref"] = store.get("vending_machine_id")
            item["lon"] = store.get("longitude")
            item["lat"] = store.get("latitude")
            item["extras"]["addr:province"] = store.get("prefecture")
            item["city"] = store.get("city")
            item["street_address"] = store.get("address")

            apply_category(Categories.VENDING_MACHINE, item)
            yield item
