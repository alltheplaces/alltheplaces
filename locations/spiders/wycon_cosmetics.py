import json
import re
from typing import AsyncIterator, Iterable, Iterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class WyconCosmeticsSpider(Spider):
    name = "wycon_cosmetics"
    item_attributes = {"brand": "Wycon Cosmetics", "brand_wikidata": "Q55831243"}
    start_urls = ["https://www.wyconcosmetics.com/pages/store-locator"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_config)

    def parse_config(self, response: TextResponse) -> Iterable[JsonRequest]:
        locator_data = json.loads(re.search(r"var locatorData = (\{.*?\}) \|\| \{\};", response.text, re.S).group(1))
        metaobject = json.loads(re.search(r"var BSS_SL_metaobject = (\{.*?\});", response.text, re.S).group(1))

        aliases = "\n".join(
            f'v{i}: metaobject(handle: {{handle: "bss_sl_metaobject_data", type: "$app:bss_sl_data_v{i}"}}) '
            "{ fields { key value } }"
            for i in range(1, (locator_data.get("maxVersion") or 1) + 1)
        )
        yield JsonRequest(
            url=f"https://{locator_data['domain']}/api/{metaobject['apiVersion']}/graphql.json",
            headers={"X-Shopify-Storefront-Access-Token": metaobject["storefrontAccessToken"]},
            data={"query": "{" + aliases + "}"},
            callback=self.parse,
        )

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Feature]:
        for store in self.extract_stores(response.json()["data"]):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("WYCON cosmetics ")
            item["street_address"] = merge_address_lines([item.pop("addr_full", None), store["additional_address"]])
            item["country"] = item.pop("state")
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item

    @staticmethod
    def extract_stores(data: dict) -> Iterator[dict]:
        """Stores are chunked across the "locations_N" fields of each version's metaobject."""
        for fields in DictParser.iter_matching_keys(data, "fields"):
            for field in fields:
                if field["value"] and field["key"].startswith("locations_"):
                    yield from json.loads(field["value"])["data"]
