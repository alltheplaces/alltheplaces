from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LarosasSpider(SitemapSpider, StructuredDataSpider):
    name = "larosas"
    item_attributes = {"brand": "Larosa's", "brand_wikidata": "Q6460833"}
    sitemap_urls = ["https://www.larosas.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]
