from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class Via313Spider(SitemapSpider, StructuredDataSpider):
    name = "via313"
    item_attributes = {
        "brand": "Via 313",
        "brand_wikidata": "Q115699944",
        "nsi_id": "-1",
        "extras": {**Categories.RESTAURANT.value, "cuisine": "pizza"},
    }
    sitemap_urls = ["https://locations.via313.com/robots.txt"]
    sitemap_rules = [(r"/locations/\d+-[-\w]+/", "parse_sd")]
