import json

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class ReiSpider(SitemapSpider, StructuredDataSpider):
    name = "rei"
    item_attributes = {"brand": "REI", "brand_wikidata": "Q3414933", "country": "US"}
    allowed_domains = ["www.rei.com"]
    sitemap_urls = ["https://www.rei.com/sitemap-stores.xml"]
    sitemap_rules = [(r"^https://www.rei.com/stores/[^/]+$", "parse_sd")]
    user_agent = BROWSER_DEFAULT
    download_delay = 2.5
    wanted_types = ["Store"]
