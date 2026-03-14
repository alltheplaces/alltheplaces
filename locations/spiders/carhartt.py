from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CarharttSpider(SitemapSpider, StructuredDataSpider):
    name = "carhartt"
    item_attributes = {"brand": "Carhartt", "brand_wikidata": "Q527877"}
    allowed_domains = ["carhartt.com"]
    sitemap_urls = ["https://stores.carhartt.com/robots.txt"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["ClothingStore"]
    drop_attributes = {"image"}
