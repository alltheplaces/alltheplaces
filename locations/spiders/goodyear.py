from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoodYearSpider(SitemapSpider, StructuredDataSpider):
    name = "goodyear"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    sitemap_urls = [
        "https://www.goodyear.com/sitemap-retail-detail.xml",
        "https://www.goodyearautoservice.com/sitemap-retail-detail.xml",
    ]
    sitemap_rules = [("/tire-shop/", "parse_sd"), ("/shop/", "parse_sd")]
