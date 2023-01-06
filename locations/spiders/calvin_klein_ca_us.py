from scrapy.spiders import SitemapSpider

from locations.spiders.calvin_klein import CalvinKleinSpider
from locations.structured_data_spider import StructuredDataSpider


class CalvinKleinCAUSSpider(SitemapSpider, StructuredDataSpider):
    name = "calvin_klein_us"
    item_attributes = CalvinKleinSpider.item_attributes
    sitemap_urls = ["https://stores.calvinklein.us/robots.txt"]
    sitemap_rules = [(r"https://stores\.calvinklein\.us/\w\w/[-\w]+/\d+/", "parse_sd")]
    json_parser = "json5"
