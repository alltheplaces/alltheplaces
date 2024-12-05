from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class GoldsGymSpider(SitemapSpider):
    name = "golds_gym"
    item_attributes = {"brand": "Gold's Gym", "brand_wikidata": "Q1536234"}
    sitemap_urls = ["https://www.goldsgym.com/gym-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//h1").xpath("normalize-space()").get()
        item["addr_full"] = response.xpath('//*[@class = "block-content__address"]//text()').get()
        item["website"] = item["ref"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["lat"] = response.xpath("//@data-map-lat").get()
        item["lon"] = response.xpath("//@data-map-lng").get()
        yield item
