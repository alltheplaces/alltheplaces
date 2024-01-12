from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import extract_phone


class TacoBellESSpider(SitemapSpider):
    name = "taco_bell_es"
    item_attributes = {"brand": "Taco Bell", "brand_wikidata": "Q752941"}
    sitemap_urls = ["https://tacobell.es/restaurantes-sitemap.xml"]
    sitemap_rules = [("/restaurantes/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = clean_address(response.xpath('//div[@class="dir"]/h1/text()').getall())
        item["addr_full"] = clean_address(response.xpath('//div[@class="dir"]/text()').getall())
        extract_google_position(item, response)
        extract_phone(item, response)

        yield item
