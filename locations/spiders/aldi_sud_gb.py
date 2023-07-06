from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AldiSudGB(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_gb"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672", "country": "GB"}
    allowed_domains = ["aldi.co.uk"]
    sitemap_urls = ["https://stores.aldi.co.uk/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    user_agent = BROWSER_DEFAULT
