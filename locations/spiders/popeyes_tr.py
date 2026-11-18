import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class PopeyesTRSpider(SitemapSpider):
    name = "popeyes_tr"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}
    sitemap_urls = ["https://www.popeyes.com.tr/robots.txt"]
    sitemap_rules = [(r"/subeler/[^/]+/[^/]+/[^/]+$", "parse")]
    sitemap_follow = ["restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//title/text()").get("").removeprefix("Popeyes® ").split("|", 1)[0].strip()
        item["state"] = response.xpath("//@data-city").get()
        item["city"] = response.xpath("//@data-county").get()
        item["street_address"] = response.xpath('//*[@class="restaurant-content"]/p/text()').get("")
        item["lat"], item["lon"] = json.loads(response.xpath("//@data-location").get(""))
        apply_category(Categories.FAST_FOOD, item)
        yield item
