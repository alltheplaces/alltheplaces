from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DelTacoUSSpider(SitemapSpider, StructuredDataSpider):
    name = "del_taco_us"
    item_attributes = {"brand": "Del Taco", "brand_wikidata": "Q1183818"}
    allowed_domains = ["locations.deltaco.com"]
    sitemap_urls = ["https://locations.deltaco.com/robots.txt"]
    sitemap_rules = [(r"com/us/\w\w/[^/]+\/[^/]+$", "parse")]
    wanted_types = ["Restaurant"]
    json_parser = "chompjs"
