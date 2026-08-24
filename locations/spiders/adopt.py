from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AdoptSpider(SitemapSpider, StructuredDataSpider):
    name = "adopt"
    item_attributes = {
        "brand": "Adopt'",
        "brand_wikidata": "Q104649177",
    }
    sitemap_urls = ["https://www.adopt.com/en/sitemap/sitemap.xml"]
    sitemap_rules = [
        (r"/store-locator/", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
    drop_attributes = ["facebook"]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_PERFUMERY, item)

        item["branch"] = item.pop("name", "").removeprefix("Adopt Parfums ")

        yield item
