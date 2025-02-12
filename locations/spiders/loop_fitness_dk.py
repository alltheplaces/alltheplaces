from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LoopFitnessDKSpider(SitemapSpider, StructuredDataSpider):
    name = "loop_fitness_dk"
    item_attributes = {"brand": "LOOP Fitness", "brand_wikidata": "Q18647221"}
    sitemap_urls = ["https://loopfitness.dk/fitness-center-sitemap.xml"]
    sitemap_rules = [(r"/centre/loop-fitness", "parse_sd")]
    wanted_types = ["Place"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("LOOP Fitness ")

        yield item
