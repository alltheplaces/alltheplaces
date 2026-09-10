from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CarglassFRSpider(SitemapSpider, StructuredDataSpider):
    name = "carglass_fr"
    item_attributes = {"brand": "Carglass", "brand_wikidata": "Q1035997"}
    sitemap_urls = ["https://www.carglass.fr/centre/sitemap.xml"]
    wanted_types = ["AutoRepair"]
    drop_attributes = ["facebook", "phone", "twitter"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # drop duplicate item containing no information
        if not ld_data.get("geo"):
            return
        # drop locations that inside norauto car repair shops, the brand of these shops is norauto and already collected by norauto_fr spider
        if item.get("street_address") and item["street_address"].lower() == "norauto":
            return

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        item["branch"] = (item.pop("name", "") or "").removeprefix("Carglass® ")
        yield item
