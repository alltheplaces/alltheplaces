from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PrimaprixSpider(SitemapSpider, StructuredDataSpider):
    name = "primaprix"
    item_attributes = {"brand": "Primaprix", "brand_wikidata": "Q112691161"}
    allowed_domains = ["primaprix.eu"]
    sitemap_urls = ["https://primaprix.eu/sitemap_index.xml"]
    sitemap_rules = [(r"https://primaprix.eu/tienda/[^/]+/", "parse_sd")]
    time_format = "%H:%M:%S"
