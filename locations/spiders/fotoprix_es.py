from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FotoprixESSpider(SitemapSpider, StructuredDataSpider):
    name = "fotoprix_es"
    item_attributes = {
        "brand": "Fotoprix",
        "brand_wikidata": "Q99196842",
    }
    sitemap_urls = ["https://www.fotoprix.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.fotoprix.com/tiendas/[\w-]+/[\w-]+", "parse"),
    ]
