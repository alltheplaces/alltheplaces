from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROSWER_DEFAULT


class AldiSudGB(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_gb"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672", "country": "GB"}
    allowed_domains = ["aldi.co.uk"]
    download_delay = 10
    sitemap_urls = ["https://www.aldi.co.uk/sitemap/store-en_gb-gbp"]
    sitemap_rules = [("", "parse_sd")]
    user_agent = BROSWER_DEFAULT
