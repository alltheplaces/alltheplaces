from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SuperaSpider(CrawlSpider):
    name = "supera"
    item_attributes = {"brand": "Supera", "brand_wikidata": ""}
    start_urls = ["https://www.centrosupera.com/centros/"]
    rules = [Rule(LinkExtractor(restrict_xpaths="//li//a[@id]"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//meta[@property="og:title"]/@content').get()
        item["street_address"] = clean_address(
            response.xpath('//*[contains(@class,"localizacion")]//p[2]/text()').get()
        )
        item["email"] = response.xpath('//*[contains(@class,"contacto")]//p[2]/text()').get("").strip()
        if "centrosupera.com" in response.url:
            item["country"] = "ES"
        apply_category(Categories.GYM, item)
        yield item
