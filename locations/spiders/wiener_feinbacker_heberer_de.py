import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.spiders.galeria_de import GaleriaDESpider
from locations.spiders.hit_de import HitDESpider
from locations.spiders.kaufland import KauflandSpider
from locations.spiders.rewe_de import ReweDESpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class WienerFeinbackerHebererDESpider(WPStoreLocatorSpider):
    name = "wiener_feinbacker_heberer_de"
    item_attributes = {
        "brand": "Wiener Feinbäcker Heberer",
        "brand_wikidata": "Q15854357",
        "extras": Categories.SHOP_BAKERY.value,
    }
    allowed_domains = ["heberer.de"]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)

        if len(item["name"].split(" (")) > 1:
            old_name = item["name"]
            item["name"], located_in_tag = old_name.split(" (", 1)
            if re.search(r"\WRewe\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = ReweDESpider.item_attributes["brand"]
                item["located_in_wikidata"] = ReweDESpider.item_attributes["brand_wikidata"]
            elif re.search(r"\WHIT\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = HitDESpider.item_attributes["brand"]
                item["located_in_wikidata"] = HitDESpider.item_attributes["brand_wikidata"]
            elif re.search(r"\WKarstadt\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = GaleriaDESpider.item_attributes["brand"]
                item["located_in_wikidata"] = GaleriaDESpider.item_attributes["brand_wikidata"]
            elif re.search(r"\WKaufland\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = KauflandSpider.item_attributes["brand"]
                item["located_in_wikidata"] = KauflandSpider.item_attributes["brand_wikidata"]
            else:
                item["name"] = old_name

        yield item
