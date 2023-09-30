from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class GreeneKingPubsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "greene_king_pubs_gb"
    item_attributes = {
        "brand": "Greene King",
        "brand_wikidata": "Q5564162",
        "extras": Categories.PUB.value,
    }
    sitemap_urls = ["https://www.greeneking.co.uk/sitemap.xml"]
    sitemap_rules = [(r"\/pubs\/([-\w]+)\/([-\w]+)\/?$", "parse_sd")]
    custom_settings = {"REDIRECT_ENABLED": False}
