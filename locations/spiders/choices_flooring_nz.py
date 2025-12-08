from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.choices_flooring_au import ChoicesFlooringAUSpider


class ChoicesFlooringNZSpider(SitemapSpider):
    name = "choices_flooring_nz"
    item_attributes = ChoicesFlooringAUSpider.item_attributes
    sitemap_urls = ["https://www.choicesflooring.co.nz/store-sitemap-xml"]
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["addr_full"] = response.xpath("//address/a/text()").get()
        item["website"] = item["ref"] = response.url
        extract_google_position(item, response)
        yield item
