from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class APlusGlassFRSpider(SitemapSpider, StructuredDataSpider):
    name = "a_plus_glass_fr"
    item_attributes = {
        "brand": "A+Glass",
        "brand_wikidata": "Q116688243",
    }
    sitemap_urls = ["https://www.aplusglass.com/service-centers-sitemap.xml"]
    sitemap_rules = [
        (r"", "parse_sd"),
    ]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        item["branch"] = item.pop("name", "").removeprefix("A+GLASS ")

        yield item
