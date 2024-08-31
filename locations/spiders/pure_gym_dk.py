from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PureGymDKSpider(SitemapSpider, StructuredDataSpider):
    name = "pure_gym_dk"
    item_attributes = {"brand": "PureGym", "brand_wikidata": "Q12311466"}
    sitemap_urls = ["https://www.puregym.dk/sitemap.xml"]
    sitemap_rules = [(r"/find-center/", "parse_sd")]
    wanted_types = ["ExerciseGym"]
