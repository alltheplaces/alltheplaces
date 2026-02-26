import re
from typing import Any, Iterable

import chompjs
from scrapy.http import JsonRequest, Response, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class McdonaldsILSpider(JSONBlobSpider):
    name = "mcdonalds_il"
    item_attributes = {"brand_wikidata": "Q12061542"}
    start_urls = ["https://order.mcdonalds.co.il"]
    locations_key = ["data", "stores"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(
            url=response.xpath('//script[contains(@src,"/_next/static/chunks/pages/_app-")]/@src').get(),
            callback=self.build_api_url,
        )

    def build_api_url(self, response: Response, **kwargs: Any) -> Any:
        api_details = chompjs.parse_js_object(
            re.search(r"\(this,[a-z],({https.+?baseUrl:\".+?})\)", response.text).group(1)
        )
        yield JsonRequest(
            url=f'https://{api_details["baseUrl"]}/{api_details["parts"]["path"]}/{api_details["parts"]["platform"]}/{api_details["parts"]["version"]}/getStores',
            callback=self.parse_locations,
        )

    def parse_locations(self, response: TextResponse) -> Any:
        yield from super().parse(response)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["StoreIndex"]
        item["branch"] = feature["StoreNameLong"]
        yield item
