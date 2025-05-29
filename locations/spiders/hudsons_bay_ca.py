from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import FIREFOX_LATEST


class HudsonsBayCASpider(Spider):
    name = "hudsons_bay_ca"
    item_attributes = {"brand": "Hudson's Bay", "brand_wikidata": "Q641129"}
    start_urls = ["https://www.thebay.com/content/store-locator"]
    user_agent = FIREFOX_LATEST
    custom_settings = {"DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"}}
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="ed-container--store"]'):
            item = Feature()
            item["branch"] = (
                location.xpath('.//h3[contains(@class, "store-name")]/text()')
                .get()
                .removeprefix("La Baie D'Hudson ")
                .removeprefix("Hudson's Bay ")
            )
            item["addr_full"] = merge_address_lines(
                location.xpath('.//p[contains(@class, "store-address")]/text()').getall()
            )
            item["phone"] = location.xpath('.//a[contains(@class, "store-phone")]/text()').get()

            yield item
