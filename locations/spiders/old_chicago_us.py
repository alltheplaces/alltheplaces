from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class OldChicagoUSSpider(SitemapSpider):
    name = "old_chicago_us"
    item_attributes = {"brand": "Old Chicago", "brand_wikidata": "Q64411347"}
    sitemap_urls = ["https://oldchicago.com/sitemap_index.xml"]
    sitemap_rules = [(r"https://oldchicago.com/locations/us/[^/]+/[^/]+/[^/]+/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h2/text()").get()
        item["street_address"] = response.xpath('//*[@class="location-address"]//a/text()').get()
        item["addr_full"] = merge_address_lines(response.xpath('//*[@class="location-address"]/a//text()').getall())
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        yield item
