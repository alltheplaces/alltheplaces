from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LoftSpider(SitemapSpider, StructuredDataSpider):
    name = "loft"
    item_attributes = {"brand": "Loft", "brand_wikidata": "Q62075137"}
    allowed_domains = ["stores.loft.com"]
    sitemap_urls = ["https://stores.loft.com/sitemap.xml"]
    sitemap_rules = [
        (r"/outlet/[-\w]{2}/[-\w]{2}/[-\w]+/[-\w]+.html$", "parse_sd"),
        (r"/[-\w]{2}/[-\w]+/[-\w]+.html$", "parse_sd"),
    ]
    wanted_types = ["ClothingStore"]
