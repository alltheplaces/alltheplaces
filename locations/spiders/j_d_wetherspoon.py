from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JDWetherspoonSpider(SitemapSpider, StructuredDataSpider):
    name = "j_d_wetherspoon"
    item_attributes = {"brand": "J D Wetherspoon", "brand_wikidata": "Q6109362"}
    allowed_domains = ["www.jdwetherspoon.com"]
    sitemap_urls = ["https://www.jdwetherspoon.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.jdwetherspoon\.com\/pubs\/all-pubs(?:\/[\w\-]+){3}", "parse_sd")]
    custom_settings = {"REDIRECT_ENABLED": False}  # Numerous location pages don't exist.
