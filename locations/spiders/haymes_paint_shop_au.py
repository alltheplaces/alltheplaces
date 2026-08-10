import re
from typing import Callable, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, JsonResponse, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class HaymesPaintShopAUSpider(Spider):
    name = "haymes_paint_shop_au"
    item_attributes = {"brand": "Haymes Paint Shop", "brand_wikidata": "Q140681622"}
    allowed_domains = ["www.haymespaint.com.au"]
    start_urls = ["https://www.haymespaint.com.au/pages/find-a-store"]
    _api_endpoint: str = "https://www.haymespaint.com.au/api/2025-01/graphql.json"

    @staticmethod
    def _request_graphql_page(
        api_endpoint: str, storefront_api_token: str, callback_function: Callable, cursor: str | None = None
    ) -> JsonRequest:
        graphql_query = """
query getStoreLocations($type: String!, $after: String, $first: Int!) {
    metaobjects(type: $type, after: $after, first: $first) {
        nodes {
            id
            handle
            fields { key value }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
"""
        graphql_variables = {
            "type": "store_details",
            "first": 250,
            "after": cursor,
        }
        data = {
            "query": graphql_query,
            "variables": graphql_variables,
        }
        yield JsonRequest(
            url=api_endpoint,
            headers={"X-Shopify-Storefront-Access-Token": storefront_api_token},
            data=data,
            method="POST",
            callback=callback_function,
            dont_filter=True,
        )

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        js_blob = response.xpath('//script[contains(text(), "STOREFRONT_API_TOKEN")]/text()').get()
        if m := re.search(r"STOREFRONT_API_TOKEN\s*=\s*'([a-f0-9]{32})'", js_blob):
            storefront_api_token = m.group(1)
            yield from self._request_graphql_page(
                api_endpoint=self._api_endpoint,
                storefront_api_token=storefront_api_token,
                callback_function=self.parse_graphql_response,
            )

    def parse_graphql_response(self, response: JsonResponse) -> Iterable[Feature | JsonRequest]:
        for store in response.json()["data"]["metaobjects"]["nodes"]:
            attributes = {x["key"]: x["value"] for x in store["fields"]}
            if attributes["storetype"] != "ST":
                # Ignore stockists
                continue
            properties = {
                "ref": attributes["prontoaccountcode"],
                "branch": attributes["business_name"].removeprefix("Haymes Paint Shop "),
                "lat": attributes["googlelocationlatitude"],
                "lon": attributes["googlelocationlongitude"],
                "addr_full": attributes["googleformattedaddress"],
                "phone": attributes["googleformattedphoneno"],
                "email": attributes["email"],
                "website": "https://www.haymespaint.com.au/pages/stores/" + store["handle"],
                "opening_hours": OpeningHours(),
            }
            hours_string = ", ".join(
                [
                    attributes.get("googlehoursmonday"),
                    attributes.get("googlehourstuesday"),
                    attributes.get("googlehourswednesday"),
                    attributes.get("googlehoursthursday"),
                    attributes.get("googlehoursfriday"),
                    attributes.get("googlehourssaturday"),
                    attributes.get("googlehourssunday"),
                ]
            )
            properties["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.SHOP_PAINT, properties)
            yield Feature(**properties)

        if response.json()["data"]["metaobjects"]["pageInfo"]["hasNextPage"]:
            storefront_api_token = response.request.headers["X-Shopify-Storefront-Access-Token"]
            cursor = response.json()["data"]["metaobjects"]["pageInfo"]["endCursor"]
            yield from self._request_graphql_page(
                api_endpoint=self._api_endpoint,
                storefront_api_token=storefront_api_token,
                callback_function=self.parse_graphql_response,
                cursor=cursor,
            )
