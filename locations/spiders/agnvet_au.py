import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AgnvetAUSpider(SitemapSpider):
    name = "agnvet_au"
    item_attributes = {"brand": "AGnVET", "brand_wikidata": "Q119263284"}
    sitemap_urls = ["https://agnvet.com.au/locations-sitemap.xml"]
    sitemap_rules = [(r"https://agnvet.com.au/locations/[^/]+/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if address_data := response.xpath("//@data-pins").get():
            item = DictParser.parse(json.loads(address_data)[0])
            item.pop("state")
            item["name"] = self.item_attributes["brand"]
            item["branch"] = response.xpath("//h1/text()").get()
            item["phone"] = response.xpath('//*[contains(@href,"tel:")]/span[2]//text()').get()
            item["website"] = item["ref"] = response.url
            apply_category(Categories.SHOP_AGRARIAN, item)
            yield item
