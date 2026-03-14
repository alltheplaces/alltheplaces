from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class BlindsToGoSpider(SitemapSpider):
    name = "blinds_to_go"
    item_attributes = {"name": "Blinds to Go", "brand": "Blinds to Go", "brand_wikidata": "Q123409913"}
    start_urls = ["https://www.blindstogo.com/en/stores"]
    sitemap_urls = ["https://www.blindstogo.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[^/]+", "parse")]
    sitemap_follow = ["store_locations"]
    skip_auto_cc_spider_name = False

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h5/text()").get("").replace("Showroom", "").strip("- ")
        item["addr_full"] = response.xpath('//*[@class="flex items-center flex-wrap"]//p//a//text()').get()
        item["phone"] = response.xpath(
            '//*[@class="flex items-center flex-wrap"]//*[contains(@href,"tel:")]/text()'
        ).get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.SHOP_WINDOW_BLIND, item)
        yield item
