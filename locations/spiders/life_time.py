from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LifeTimeSpider(SitemapSpider, StructuredDataSpider):
    name = "life_time"
    item_attributes = {"brand": "Life Time", "brand_wikidata": "Q6545004"}
    sitemap_urls = ["https://www.lifetime.life/robots.txt"]
    sitemap_rules = [(r"/life-time-locations/[-\w]+\.html$", "parse_sd")]
    wanted_types = ["ExerciseGym"]
