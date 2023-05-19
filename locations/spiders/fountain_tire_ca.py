from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FountainTireCASpider(SitemapSpider, StructuredDataSpider):
    name = "fountain_tire_ca"
    item_attributes = {"brand": "Fountain Tire", "brand_wikidata": "Q5474771"}
    sitemap_urls = ["https://www.fountaintire.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+$", "parse")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["url"] = None
