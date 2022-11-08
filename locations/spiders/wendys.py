from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WendysSpider(SitemapSpider, StructuredDataSpider):
    name = "wendys"
    item_attributes = {"brand": "Wendy's", "brand_wikidata": "Q550258"}
    sitemap_urls = ["https://locations.wendys.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.wendys.com/.+/\w\w/.+/.+", "parse_sd")]
