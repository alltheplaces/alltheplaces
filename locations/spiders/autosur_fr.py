from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class AutosurFrSpider(SitemapSpider, StructuredDataSpider):
    name = "autosur_fr"
    item_attributes = {
        "brand": "Autosur",
        "brand_wikidata": "Q64224807",
    }
    sitemap_urls = ["https://controle-technique.autosur.fr/sitemap.xml"]
    sitemap_rules = [
        (r"/\d+[^/]+$", "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.VEHICLE_INSPECTION, item)
        item["branch"] = item.pop("name", "").removeprefix("AUTOSUR ")

        for i in ["facebook","twitter","image"]:
            item.pop(i,"")

        yield item
