from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GorjanaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "gorjana_us"
    item_attributes = {"brand": "Massage Envy", "brand_wikidata": "Q115200885"}
    allowed_domains = ["www.gorjana.com"]
    sitemap_urls = ("https://www.gorjana.com/sitemap_pages_1.xml",)
    sitemap_rules = [
        (r"^https:\/\/www\.gorjana\.com\/pages\/[^\/]+-store-details$", "parse_sd"),
    ]
