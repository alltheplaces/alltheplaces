from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KiehlsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kiehls_us"
    item_attributes = {
        "brand": "Kiehl's",
        "brand_wikidata": "Q3196447",
    }
    allowed_domains = ["stores.kiehls.com"]
    sitemap_urls = ["https://stores.kiehls.com/sitemap.xml"]
    sitemap_rules = [(r"https://stores.kiehls.com\/[^/]+/[^/]+/[^/]+.html$", "parse_sd")]
    wanted_types = ["HealthAndBeautyBusiness"]
