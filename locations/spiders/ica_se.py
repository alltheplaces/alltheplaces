from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class IcaSESpider(SitemapSpider, StructuredDataSpider):
    name = "ica_se"
    item_attributes = {"brand": "ICA", "brand_wikidata": "Q1663776", "extras": Categories.SHOP_SUPERMARKET.value}
    sitemap_urls = ["https://www.ica.se/butiker/sitemaps/", "https://www.ica.se/butiker/sitemap.xml"]
    sitemap_rules = [
        (r"/butiker/.+\d+/$", "parse_sd"),
    ]
