from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SfrFRSpider(SitemapSpider, StructuredDataSpider):
    name = "sfr_fr"
    item_attributes = {"brand": "SFR", "brand_wikidata": "Q218765"}
    sitemap_urls = ["https://boutique.sfr.fr/sitemap_index.xml"]
    sitemap_rules = [(r"/france-FR/\d+/[-\w]+/details$", "parse_sd")]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if (name := item.get("name")) and name.startswith("Boutique SFR "):
            item["branch"] = name.removeprefix("Boutique SFR ")
            item["name"] = None
        apply_category(Categories.SHOP_TELECOMMUNICATION, item)
        yield item
