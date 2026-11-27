from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ShipleyDoNutsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "shipley_do_nuts_us"
    item_attributes = {
        "brand": "Shipley Do-Nuts",
        "brand_wikidata": "Q7498017",
        "name": "Shipley Do-Nuts",
    }
    sitemap_urls = ["https://shipleydonuts.com/sitemap_index.xml"]
    sitemap_rules = [(r"/locations/[^/]+$", "parse_sd")]
    wanted_types = ["Bakery"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        apply_category(Categories.FAST_FOOD, item)
        yield item
