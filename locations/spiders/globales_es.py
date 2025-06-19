from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GlobalesESSpider(SitemapSpider, StructuredDataSpider):
    name = "globales_es"
    item_attributes = {"brand": "Globales", "brand_wikidata": "Q24279046"}
    sitemap_urls = ["https://www.globales.com/en/sitemap.xml"]
    sitemap_rules = [(r"/map/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.HOTEL, item)
        item["branch"] = item.pop("name").replace("Globales ", "")
        yield item
