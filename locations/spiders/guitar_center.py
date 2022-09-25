from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class GuitarCenterSpider(SitemapSpider, StructuredDataSpider):
    name = "guitar_center"
    item_attributes = {"brand": "Guitar Center", "brand_wikidata": "Q3622794"}
    sitemap_urls = ("https://stores.guitarcenter.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://stores.guitarcenter.com/[^/]+/[^/]+/[^/]+$", "parse_sd"),
    ]
    wanted_types = ["MusicStore"]
