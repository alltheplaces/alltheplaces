from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class LoopFitnessDKSpider(SitemapSpider):
    name = "loop_fitness_dk"
    item_attributes = {"brand": "LOOP Fitness", "brand_wikidata": "Q18647221"}
    sitemap_urls = ["https://loopfitness.dk/fitness-center-sitemap.xml"]
    sitemap_rules = [(r"/centre/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        info = response.xpath('//div[@class="loop-center-info"]')
        if not info:
            return

        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = response.xpath('//h1[starts-with(@id, "h-")]/text()').get("").strip()
        item["addr_full"] = " ".join(info.xpath('.//*[@itemprop="address"]//text()').getall()).strip()
        item["phone"] = info.xpath('.//*[@itemprop="telephone"]//text()').get()
        item["email"] = info.xpath('.//*[@itemprop="email"]//text()').get()

        apply_category(Categories.GYM, item)
        yield item
