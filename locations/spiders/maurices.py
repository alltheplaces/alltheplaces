from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MauricesSpider(SitemapSpider, StructuredDataSpider):
    name = "maurices"
    item_attributes = {"brand": "maurices", "brand_wikidata": "Q6793571"}
    sitemap_urls = ["https://locations.maurices.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    download_delay = 0.2
    drop_attributes = {"image"}
