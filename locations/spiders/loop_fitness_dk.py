from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LoopFitnessDKSpider(SitemapSpider, StructuredDataSpider):
    name = "loop_fitness_dk"
    item_attributes = {"brand": "Loop Fitness", "brand_wikidata": "Q18647221"}
    sitemap_urls = ["https://loopfitness.dk/fitness-center-sitemap.xml"]
    sitemap_rules = [(r"/centre/loop-fitness", "parse_sd")]
