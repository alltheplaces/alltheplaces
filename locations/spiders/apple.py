from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AppleSpider(SitemapSpider, StructuredDataSpider):
    name = "apple"
    item_attributes = {"brand": "Apple", "brand_wikidata": "Q421253"}
    sitemap_urls = ("https://www.apple.com/retail/sitemap/sitemap.xml",)
