from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ShurgardSpider(SitemapSpider, StructuredDataSpider):
    name = "shurgard"
    item_attributes = {"brand": "Shurgard", "brand_wikidata": "Q3482670"}
    sitemap_urls = ["https://www.shurgard.com/sitemap.xml"]
    sitemap_rules = [(r"/en-(?:\w\w/self-storage-[-\w]+|[bd]e/self-storage)/[-\w]+/[-\w]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
