from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class NeonessFRSpider(SitemapSpider, StructuredDataSpider):
    name = "neoness_fr"
    item_attributes = {
        "brand": "Neoness",
        "brand_wikidata": "Q86668014",
        "extras": Categories.GYM.value,
    }
    sitemap_urls = ["https://www.neoness.fr/sitemap.xml"]
    sitemap_rules = [(r"/clubs/", "parse_sd")]
    drop_attributes = {"image", "facebook"}
