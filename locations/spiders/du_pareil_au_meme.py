from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category
import json

class DuPareilAuMemeSpider(SitemapSpider, StructuredDataSpider):
    name = "du_pareil_au_meme"
    item_attributes = {
        "brand": "Du Pareil au Même",
        "brand_wikidata": "Q3040318",
    }
    sitemap_urls = ["https://boutiques.dpam.com/sitemap_pois.xml"]
    wanted_types = ["ClothingStore"]
    sitemap_rules = [
        (r"/en/", "parse_sd"),
    ]
    drop_attributes = ["image", "facebook"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        item["branch"] = item.pop("name", "").removeprefix("Du Pareil au même ")
        yield item
