from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class GoldwagenSpider(SitemapSpider):
    name = "goldwagen"
    item_attributes = {"brand": "Goldwagen", "brand_wikidata": "Q129485065"}
    sitemap_urls = ["https://www.goldwagen.com/sitemap_index.xml"]
    sitemap_follow = ["stores-sitemap"]
    sitemap_rules = [("/store/", "parse")]
    custom_settings = {"DOWNLOAD_DELAY": 3}  # Requested by robots.txt

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//h1[@class="entry-title"]/text()').get("")
        if item["name"].startswith("Goldwagen"):
            item["branch"] = item.pop("name").removeprefix("Goldwagen").strip(" –")

        item["addr_full"] = merge_address_lines(
            response.xpath('//div[contains(@class, "store_locator_single_address")]/text()').getall()
        )
        if lat := response.xpath("//@data-lat").get():
            item["lat"] = lat
        if lon := response.xpath("//@data-lng").get():
            item["lon"] = lon

        extract_phone(item, response)
        apply_category(Categories.SHOP_CAR_PARTS, item)

        yield item
