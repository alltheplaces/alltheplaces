from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class StarbucksAESASpider(SitemapSpider, StructuredDataSpider):
    name = "starbucks_ae_sa"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    sitemap_urls = [
        "https://locations.starbucks.ae/sitemap.xml",
        "https://locations.starbucks.sa/sitemap.xml",
    ]
    sitemap_rules = [
        (r"https://locations.starbucks.ae/directory/[a-z\-]+/[a-z\-]+$", "parse_sd"),
        (r"https://locations.starbucks.sa/directory/[a-z\-]+/[a-z\-]+$", "parse_sd"),
    ]
