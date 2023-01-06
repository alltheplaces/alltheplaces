from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROSWER_DEFAULT


class HarveysSpider(SitemapSpider, StructuredDataSpider):
    name = "harveys"
    item_attributes = {"brand": "Harvey's", "brand_wikidata": "Q1466184"}
    allowed_domains = ["harveys.ca"]
    sitemap_urls = ["https://www.harveys.ca/en/locations/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["Restaurant"]
    user_agent = BROSWER_DEFAULT
