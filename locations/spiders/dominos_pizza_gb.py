from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROSWER_DEFAULT


class DominiosGB(SitemapSpider, StructuredDataSpider):
    name = "dominos_pizza_gb"
    item_attributes = {
        "brand": "Domino's Pizza",
        "brand_wikidata": "Q839466",
        "country": "GB",
    }
    sitemap_urls = ["https://www.dominos.co.uk/pizza-near-me/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.dominos\.co\.uk\/pizza-near-me\/[-.\w]+\/([-.\w]+)$",
            "parse_sd",
        )
    ]
    user_agent = BROSWER_DEFAULT
