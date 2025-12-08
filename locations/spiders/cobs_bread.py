from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CobsBreadSpider(SitemapSpider, StructuredDataSpider):
    name = "cobs_bread"
    item_attributes = {"brand": "COBS Bread", "brand_wikidata": "Q116771375"}
    allowed_domains = ["www.cobsbread.com"]
    sitemap_urls = ["https://www.cobsbread.com/bakery-sitemap.xml"]
    sitemap_rules = [(r"/local-bakery/", "parse_sd")]
