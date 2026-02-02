from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse

from locations.items import Feature
from locations.storefinders.locally import LocallySpider


class ColumbiaUSSpider(LocallySpider):
    name = "columbia_us"
    item_attributes = {"brand": "Columbia", "brand_wikidata": "Q1112588"}
    allowed_domains = ["columbia.locally.com"]
    start_urls = [
        "https://columbia.locally.com/stores/conversion_data?has_data=true&company_id=67&category=Brand&map_ne_lat=72&map_ne_lng=-50&map_sw_lat=15&map_sw_lng=-180&map_distance_diag=10000",
        "https://columbia.locally.com/stores/conversion_data?has_data=true&company_id=67&category=Factory&map_ne_lat=72&map_ne_lng=-50&map_sw_lat=15&map_sw_lng=-180&map_distance_diag=10000",
        "https://columbia.locally.com/stores/conversion_data?has_data=true&company_id=67&category=clearancestore&map_ne_lat=72&map_ne_lng=-50&map_sw_lat=15&map_sw_lng=-180&map_distance_diag=10000",
    ]

    async def start(self) -> AsyncIterator[Request]:
        # LocallySpider requires exactly one URL, so looping over the different start_urls.
        for url in self.start_urls:
            yield Request(url=url)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        yield item
