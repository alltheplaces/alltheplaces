import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ChaussonMateriauxFRSpider(SitemapSpider, StructuredDataSpider):
    name = "chausson_materiaux_fr"
    item_attributes = {"brand": "Chausson Matériaux", "brand_wikidata": "Q100701530"}
    sitemap_urls = ["https://www.chausson.fr/sitemap-agencies.xml"]
    sitemap_rules = [(r"/agences/\d+$", "parse_sd")]
    wanted_types = ["Store"]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        item["branch"] = re.sub(r"^Chausson\s+Mat[ée]riaux\s+", "", item.pop("name"), flags=re.IGNORECASE)
        if postcode := item.get("postcode"):
            # Leading zero is dropped for departments 01 to 09
            item["postcode"] = postcode.zfill(5)

        # Each agency has one specialty, e.g. "Généraliste", "Réseaux TP", "Bois Couverture" or "Showroom"
        specialty = response.xpath('//span[contains(@class, "agency-specialty")]/text()').get("").strip()
        if specialty == "Showroom":
            # Tile and bathroom showrooms open to the public
            apply_category(Categories.SHOP_TILES, item)
        else:
            apply_category(Categories.SHOP_TRADE, item)
            apply_category(Categories.TRADE_BUILDING_SUPPLIES, item)

        yield item
