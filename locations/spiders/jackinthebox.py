from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class JackInTheBoxSpider(SitemapSpider, StructuredDataSpider):
    name = "jackinthebox"
    item_attributes = {"brand": "Jack in the Box", "brand_wikidata": "Q1538507"}
    sitemap_urls = ["https://locations.jackinthebox.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    download_delay = 0.5
