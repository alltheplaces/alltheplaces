from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MichaelkorsSpider(SitemapSpider, StructuredDataSpider):
    name = "michaelkors"
    item_attributes = {"brand": "Michael Kors", "brand_wikidata": "Q19572998"}
    sitemap_urls = ["https://locations.michaelkors.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.michaelkors.com/.+/.+/.+/.+.html$", "parse_sd")]
