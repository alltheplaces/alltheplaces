from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class UpsStoreSpider(SitemapSpider, StructuredDataSpider):
    name = "upsstore"
    item_attributes = {"brand": "UPS Store", "brand_wikidata": "Q7771029"}
    allowed_domains = ["locations.theupsstore.com"]
    sitemap_urls = ["https://locations.theupsstore.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/locations.theupsstore.com\/[a-z]{2}\/[a-z]+\/\d+-[a-z-]+$", "parse_sd")]
    download_delay = 0.5
