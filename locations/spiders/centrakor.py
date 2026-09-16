from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Source JSON-LD hardcodes addressCountry to "FR" for these French overseas department/
# collectivity stores, but each has its own ISO country distinct from mainland France.
COUNTRY_OVERRIDES = {
    "https://www.centrakor.com/magasin-centrakor/ctkstemari/centrakor-sainte-marie-97438.html#store": "RE",
    "https://www.centrakor.com/magasin-centrakor/ctkpierrsa/centrakor---zoe-confetti-st-pierre-97410.html#store": "RE",
    "https://www.centrakor.com/magasin-centrakor/ctkleport/centrakor-le-port-97420.html#store": "RE",
    "https://www.centrakor.com/magasin-centrakor/ctkmoudong/centrakor-moudong-97122.html#store": "GP",
    "https://www.centrakor.com/magasin-centrakor/ctklesabym/centrakor-les-abymes-97139.html#store": "GP",
    "https://www.centrakor.com/magasin-centrakor/ctkbaillif/centrakor-baillif-97100.html#store": "GP",
    "https://www.centrakor.com/magasin-centrakor/ctkcarribe/the-caribbean'touch-saint-martin-97150.html#store": "MF",
    "https://www.centrakor.com/magasin-centrakor/ctklerober/centrakor-le-robert-97231.html#store": "MQ",
    "https://www.centrakor.com/magasin-centrakor/ctklemarin/centrakor-le-marin-97290.html#store": "MQ",
    "https://www.centrakor.com/magasin-centrakor/ctklelamen/centrakor-le-lamentin-97232.html#store": "MQ",
    "https://www.centrakor.com/magasin-centrakor/ctkducos/centrakor-ducos-97224.html#store": "MQ",
    "https://www.centrakor.com/magasin-centrakor/ctkcayenne/centrakor-cayenne-97300.html#store": "GF",
    "https://www.centrakor.com/magasin-centrakor/ctkdumbea/centrakor-dumbea-98835.html#store": "NC",
}


class CentrakorSpider(SitemapSpider, StructuredDataSpider):
    name = "centrakor"
    item_attributes = {"brand": "Centrakor", "brand_wikidata": "Q64079345", "name": "Centrakor"}
    sitemap_urls = ["https://www.centrakor.com/sitemaps/default/stores-sitemap.xml"]
    sitemap_rules = [(r"/magasin-centrakor/", "parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        for prefix in ("Centrakor / ", "Centrakor ", "CENTRAKOR "):
            # Some franchisees submit their store's name in all caps
            if branch.startswith(prefix):
                branch = branch[len(prefix) :]
                break
        item["branch"] = branch

        if country := COUNTRY_OVERRIDES.get(item["ref"]):
            item["country"] = country

        if item.get("email") in ("adv.site@centrakor.com", "support.achat@cid-sa.com"):
            # Corporate/regional-office addresses shared across many stores, not location-specific
            item.pop("email")

        if item.get("image") and "logo" in item["image"]:
            # Generic brand logo used when a store hasn't uploaded its own photo
            item.pop("image")

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
        yield item
