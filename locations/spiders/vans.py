from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class VansSpider(SitemapSpider, StructuredDataSpider):
    name = "vans"
    item_attributes = {"brand": "Vans", "brand_wikidata": "Q1135366"}
    allowed_domains = ["vans.com"]
    sitemap_urls = ["https://www.vans.com/sitemaps/store-locations.xml"]
    sitemap_rules = [(r"/stores/.+/.+/\w+\d+$", "parse_sd")]
    drop_attributes = {"image"}
