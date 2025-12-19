from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EconofitnessCASpider(SitemapSpider, StructuredDataSpider):
    name = "econofitness_ca"
    item_attributes = {"brand": "Éconofitness", "brand_wikidata": "Q123073582"}
    start_urls = ["https://econofitness.ca/robots.txt"]
    sitemap_urls = ["https://econofitness.ca/robots.txt"]
    sitemap_rules = [(r"/gym/", "parse_sd")]
