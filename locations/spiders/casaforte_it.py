from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CasaforteITSpider(SitemapSpider, StructuredDataSpider):
    name = "casaforte_it"
    item_attributes = {"brand": "Casaforte", "name": "Casaforte"}
    sitemap_urls = ["https://www.casaforte.it/sitemap.xml"]
    sitemap_rules = [(r"/it/dove-trovarci/[^/]+$", "parse_sd")]
    drop_attributes = {"facebook", "image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Casaforte ")
        if item.get("phone") and item["phone"].replace(" ", "").endswith("800363000"):
            item["phone"] = None
        item["ref"] = response.url
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
