from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AcademySpider(SitemapSpider, StructuredDataSpider):
    sitemap_rules = [("", "parse_sd")]
    name = "academy"
    item_attributes = {
        "brand": "Academy Sports + Outdoors",
        "brand_wikidata": "Q4671380",
    }
    sitemap_urls = [
        "https://www.academy.com/sitemap_store_1.xml.gz",
    ]
