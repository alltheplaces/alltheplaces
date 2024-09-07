from typing import Iterable

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature

# A less common wordpress based storefinder, characterised by
# - POST of search params to "action": "get_stores",
# - Two letter variables in the results, like "na"
#
# To use, specify `domain` and `lat`, `lon` as the start point.
# TODO: Rename this spider when we identify the storelocator


class WordpressHeronFoodsSpider(Spider):
    custom_settings = {"ROBOTSTXT_OBEY": False}
    domain = None
    radius = 600
    lat = None
    lon = None

    def start_requests(self):
        yield scrapy.FormRequest(
            url=f"https://{self.domain}/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_stores",
                "lat": str(self.lat),
                "lng": str(self.lon),
                "radius": str(self.radius),
            },
            callback=self.parse,
            headers={"Referer": f"https://{self.domain}/storelocator/"},
        )

    def parse(self, response):
        stores = response.json()
        for i in range(0, len(stores)):
            store = stores[str(i)]
            self.pre_process_data(store)

            properties = {
                "lat": store["lat"],
                "lon": store["lng"],
                "name": store["na"],
                "street_address": store["st"].strip(" ,"),
                "city": store["ct"].strip(),
                "postcode": store["zp"].strip(),
                "website": store["gu"],
                "ref": store["ID"],
            }

            item = Feature(**properties)
            yield from self.post_process_item(item, response, store)

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
