from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EosFitnessUSSpider(SitemapSpider, StructuredDataSpider):
    name = "eos_fitness_us"
    item_attributes = {"brand": "EōS Fitness", "brand_wikidata": "Q127770873"}
    sitemap_urls = ["https://www.eosfitness.com/robots.txt"]
    sitemap_rules = [("/gym/", "parse")]
    wanted_types = ["ExerciseGym"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "Coming Soon" in response.xpath("//head/title/text()").get(""):
            return
        apply_category(Categories.GYM, item)
        yield item
