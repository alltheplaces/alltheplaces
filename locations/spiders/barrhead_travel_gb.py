from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


# Sitemap has store links but not complete.
class BarrheadTravelGBSpider(CrawlSpider):
    name = "barrhead_travel_gb"
    item_attributes = {"brand": "Barrhead Travel", "brand_wikidata": "Q114292485"}
    start_urls = ["https://www.barrheadtravel.co.uk/storelocator"]
    rules = [Rule(LinkExtractor(allow=r"/storelocator/.+"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = (
            response.xpath('//meta[@property="og:title"]/@content')
            .get()
            .split(" | ")[0]
            .removeprefix("Barrhead Travel")
            .strip()
        )
        store_info = response.xpath("//@data-anchor/ancestor::tbody//p[1]/text()").getall()
        address_last_index = 0
        for index, text in enumerate(store_info):
            if "day" in text:
                address_last_index = index - 1
                break
        item["street_address"] = merge_address_lines(store_info[: address_last_index + 1])
        item["phone"] = response.xpath('//*[contains(text(), "Call Us")]/ancestor::p/text()').get()
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/text()').get()
        extract_google_position(item, response)
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        yield item
