from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AldiSudIE(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_ie"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672", "country": "IE"}
    allowed_domains = ["aldi.ie"]
    sitemap_urls = ["https://stores.aldi.ie/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    user_agent = BROWSER_DEFAULT
