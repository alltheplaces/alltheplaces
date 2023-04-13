from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BassettFurnitureSpider(SitemapSpider, StructuredDataSpider):
    name = "bassett_furniture"
    item_attributes = {"brand": "Bassett Furniture", "brand_wikidata": "Q4868109"}
    allowed_domains = ["stores.bassettfurniture.com"]
    sitemap_urls = ["https://stores.bassettfurniture.com/robots.txt"]
    sitemap_rules = [(r"https://stores\.bassettfurniture\.com/[-\w]+/[-\w]+/\d+/$", "parse_sd")]
    wanted_types = ["FurnitureStore"]
    json_parser = "json5"
