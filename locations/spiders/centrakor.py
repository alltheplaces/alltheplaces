from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Source JSON-LD hardcodes addressCountry to "FR" for French overseas department/collectivity
# stores too, but each has its own ISO country distinct from mainland France, identifiable from
# the postcode. "971"/"972" cover both a department and a smaller collectivity that split off it
# in 2007 but kept the same postcode prefix, so those two need an exact-postcode check first.
FR_OVERSEAS_POSTCODE_EXCEPTIONS = {"97150": "MF", "97133": "BL"}  # Saint-Martin, Saint-Barthélemy
FR_OVERSEAS_POSTCODE_PREFIXES = {
    "971": "GP",  # Guadeloupe
    "972": "MQ",  # Martinique
    "973": "GF",  # Guyane
    "974": "RE",  # Réunion
    "975": "PM",  # Saint-Pierre-et-Miquelon
    "976": "YT",  # Mayotte
    "986": "WF",  # Wallis-et-Futuna
    "987": "PF",  # Polynésie française
    "988": "NC",  # Nouvelle-Calédonie
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

        if item.get("country") == "FR" and (postcode := item.get("postcode")):
            country = FR_OVERSEAS_POSTCODE_EXCEPTIONS.get(postcode) or FR_OVERSEAS_POSTCODE_PREFIXES.get(postcode[:3])
            if country:
                item["country"] = country

        if item.get("email") in ("adv.site@centrakor.com", "support.achat@cid-sa.com"):
            # Corporate/regional-office addresses shared across many stores, not location-specific
            item.pop("email")

        if item.get("image") and "logo" in item["image"]:
            # Generic brand logo used when a store hasn't uploaded its own photo
            item.pop("image")

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
        yield item
