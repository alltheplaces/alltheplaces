from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class UpsStoreSpider(SitemapSpider, StructuredDataSpider):
    name = "ups_store"
    item_attributes = {"brand": "The UPS Store", "brand_wikidata": "Q7771029"}
    allowed_domains = ["locations.theupsstore.com"]
    sitemap_urls = ["https://locations.theupsstore.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/locations.theupsstore.com\/[a-z]{2}\/[a-z]+\/\d+-[a-z-]+$", "parse_sd")]
