from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TchipFRSpider(SitemapSpider, StructuredDataSpider):
    name = "tchip_fr"
    item_attributes = {"brand": "Tchip", "brand_wikidata": "Q62871250"}
    sitemap_urls = ["https://salons.tchip.fr/sitemap.xml"]
    sitemap_rules = [(r"https://salons\.tchip\.fr/\d+/.+$", "parse_sd")]
    wanted_types = ["HairSalon"]
    drop_attributes = {"image", "state"}
    convert_microdata = False  # page also carries a partial microdata block duplicating the JSON-LD

    # A handful of salons carry this exact pair of coordinates, which is the
    # approximate geographic centre of mainland France rather than a real
    # geocode, e.g. for a salon on Réunion (postcode 974xx).
    BAD_COORDINATES = (46.227638, 2.213749)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if (item["lat"], item["lon"]) == self.BAD_COORDINATES:
            item["lat"] = item["lon"] = None
        if (item.get("name") or "").startswith("Tchip Coiffure "):
            item["branch"] = item.pop("name").removeprefix("Tchip Coiffure ")
        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item
