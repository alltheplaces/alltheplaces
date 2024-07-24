from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TgiFridaysGRSpider(SitemapSpider, StructuredDataSpider):
    name = "tgi_fridays_gr"
    item_attributes = {"brand": "TGI Fridays", "brand_wikidata": "Q1524184"}
    sitemap_urls = [
        "https://www.fridays.gr/page-sitemap.xml",
    ]
    sitemap_rules = [("/en/restaurants/", "parse_sd")]
