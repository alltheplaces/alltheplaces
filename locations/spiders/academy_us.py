from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AcademyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "academy_us"
    item_attributes = {"brand": "Academy Sports + Outdoors", "brand_wikidata": "Q4671380"}
    sitemap_urls = ["https://www.academy.com/robots.txt"]
    sitemap_follow = ["storelocator"]
    sitemap_rules = [(r"/store-\d+$", "parse_sd")]
    wanted_types = ["SportingGoodsStore"]
