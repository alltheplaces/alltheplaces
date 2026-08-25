from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class NozFRSpider(SitemapSpider, StructuredDataSpider):
    name = "noz_fr"
    item_attributes = {
        "brand": "NOZ",
        "brand_wikidata": "Q3345688",
    }
    sitemap_urls = ["https://www.noz.fr/map-location-sitemap.xml"]
    sitemap_rules = [
        (r"", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
    drop_attributes = ["facebook"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        item["branch"] = item.pop("name", "").removeprefix("NOZ ")

        yield item
