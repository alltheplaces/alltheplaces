from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class FarmboyCASpider(SitemapSpider):
    name = "farmboy_ca"
    item_attributes = {"brand": "Farmboy", "brand_wikidata": "Q5435469"}
    allowed_domains = ["www.farmboy.ca"]
    sitemap_urls = ["https://www.farmboy.ca/stores-sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//title/text()").get("").split("|")[0].removeprefix("Farm Boy ").strip()
        item["addr_full"] = response.xpath('//*[@class="address"]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        yield item
