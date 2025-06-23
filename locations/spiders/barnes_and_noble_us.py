import json
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.geo import city_locations


class BarnesAndNobleUSSpider(Spider):
    name = "barnes_and_noble_us"
    item_attributes = {"brand": "Barnes & Noble", "brand_wikidata": "Q795454"}
    allowed_domains = [
        "stores.barnesandnoble.com",
    ]

    def start_requests(self):
        for city in city_locations("US", 15000):
            yield Request(
                url=f'https://stores.barnesandnoble.com/?searchText={city["name"]}'.replace(" ", "+"),
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in (
            json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]
            .get("stores", {})
            .get("content", [])
        ):
            item = DictParser.parse(store)
            # When both address1, address2 fields are present, address1 is venue/mall name else street address.
            item["street_address"] = store.get("address2") or store.get("address1")
            item["website"] = f'https://stores.barnesandnoble.com/store/{item["ref"]}'
            yield item
