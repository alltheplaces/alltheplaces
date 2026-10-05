from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BluespaceESSpider(SitemapSpider, StructuredDataSpider):
    name = "bluespace_es"
    item_attributes = {"brand": "Bluespace", "name": "Bluespace"}
    sitemap_urls = ["https://www.bluespace.es/businessplace-sitemap.xml"]
    sitemap_rules = [(r"/alquiler-trasteros/[^/]+/centro/[^/]+/?$", "parse_sd")]
    drop_attributes = {"facebook", "twitter", "image", "phone"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Bluespace ")
        item["website"] = response.url
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
