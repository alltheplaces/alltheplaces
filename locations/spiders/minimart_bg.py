from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.google_url import url_to_coords
from locations.items import Feature


class MinimartBGSpider(Spider):
    name = "minimart_bg"
    item_attributes = {"brand": "Minimart", "brand_wikidata": "Q119168386"}
    allowed_domains = ["mini-mart.bg", "goo.gl"]
    start_urls = ["https://mini-mart.bg/nameri-magazin/"]
    custom_settings = {"REDIRECT_ENABLED": False}
    handle_httpstatus_list = [302]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//div[contains(@class, 'et_pb_with_border')]"):
            item = Feature()
            item["addr_full"] = location.xpath(".//p//text()").get()
            location_url = location.xpath(".//a/@href").get()
            if location_url is not None:
                yield Request(method="HEAD", url=location_url, meta={"item": item}, callback=self.parse_maps_url)

    # Follow shortened URL to find full Google Maps URL containing coordinates
    def parse_maps_url(self, response):
        item = response.meta["item"]
        item["lat"], item["lon"] = url_to_coords(str(response.headers["Location"]))
        yield item
