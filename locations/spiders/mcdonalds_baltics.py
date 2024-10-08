from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBalticsSpider(SitemapSpider):
    name = "mcdonalds_baltics"
    item_attributes = McdonaldsSpider.item_attributes
    sitemap_urls = [
        "https://mcdonalds.ee/location-sitemap.xml",
        "https://mcd.lt/wp-sitemap-posts-location-1.xml",
        "https://mcdonalds.lv/location-sitemap.xml",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//h1/text()").get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//p/a[contains(@href, "tel:")]/parent::p/text()').getall()
        )
        item["phone"] = response.xpath('//p/a[contains(@href, "tel:")]/text()').get()
        item["lat"] = response.xpath("//@data-lat").extract_first()
        item["lon"] = response.xpath("//@data-lng").extract_first()
        yield item
