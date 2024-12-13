from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class SalvationArmyGBSpider(SitemapSpider):
    name = "salvation_army_gb"
    item_attributes = {"brand": "Salvation Army", "brand_wikidata": "Q188307"}
    sitemap_urls = ["https://www.salvationarmy.org.uk/robots.txt"]
    sitemap_rules = [(r"^https:\/\/www\.salvationarmy\.org\.uk\/[^/]+-charity-shop(?:-\d+)?$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["street"] = response.xpath('//*[@class="address-line1"]/text()').get()
        item["city"] = response.xpath('//*[@class="locality"]/text()').get()
        item["postcode"] = response.xpath('//*[@class="postal-code"]/text()').get()
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        apply_category(Categories.SHOP_CHARITY, item)
        yield item
