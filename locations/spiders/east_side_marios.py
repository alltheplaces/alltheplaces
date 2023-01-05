from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROSWER_DEFAULT


class EastSideMariosSpider(SitemapSpider, StructuredDataSpider):
    name = "east_side_marios"
    item_attributes = {"brand": "East Side Mario's", "brand_wikidata": "Q5329375"}
    allowed_domains = ["eastsidemarios.com"]
    sitemap_urls = ["https://www.eastsidemarios.com/en/locations/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["Restaurant"]
    user_agent = BROSWER_DEFAULT
    requires_proxy = True
