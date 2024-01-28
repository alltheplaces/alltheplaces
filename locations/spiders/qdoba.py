from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class QdobaSpider(SitemapSpider, StructuredDataSpider):
    name = "qdoba"
    item_attributes = {"brand": "Qdoba", "brand_wikidata": "Q1363885"}
    allowed_domains = ["qdoba.com"]
    sitemap_urls = ["https://locations.qdoba.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/\w\w/[^/]+/[^/]+\.html", "parse")]
    wanted_types = ["Restaurant"]
