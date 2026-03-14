from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class PlusFitnessSpider(SitemapSpider, StructuredDataSpider):
    name = "plus_fitness"
    item_attributes = {"brand": "Plus Fitness", "brand_wikidata": "Q118315364"}
    sitemap_urls = [
        "https://www.plusfitness.com.au/sitemap.xml",
        "https://www.plusfitness.co.in/sitemap.xml",
        "https://www.plusfitness.co.nz/sitemap.xml",
    ]
    sitemap_rules = [(r"/gyms/.+", "parse_sd")]
    wanted_types = ["ExerciseGym"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        yield item
