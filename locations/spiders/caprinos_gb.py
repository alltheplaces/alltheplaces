from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CaprinosGBSpider(Spider):
    name = "caprinos_gb"
    item_attributes = {"brand": "Caprinos", "brand_wikidata": "Q125623745"}
    start_urls = ["https://www.caprinospizza.co.uk/api/get_restaurant_urls"]  # No API provides addresses
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ref, url in response.json()["restaurant_urls"].items():
            yield Request(
                url=urljoin(url, "/contact"),
                callback=self.parse_location,
                cb_kwargs=dict(ref=ref),
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = kwargs["ref"]
        item["website"] = response.url
        item["addr_full"] = clean_address(
            response.xpath(
                '//*[@class="shop-info__feature-title"][contains(text(), "Address")]/following-sibling::div/text()'
            ).getall()[:2]
        )
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get()
        extract_google_position(item, response)
        yield item
