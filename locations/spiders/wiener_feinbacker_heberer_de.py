import re
from html import unescape

from scrapy import Selector

from locations.categories import Categories
from locations.hours import DAYS_DE, OpeningHours
from locations.spiders.galeria_de import GaleriaDESpider
from locations.spiders.hit_de import HITDESpider
from locations.spiders.kaufland import KauflandSpider
from locations.spiders.rewe_de import REWEDESpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class WienerFeinbackerHebererDESpider(WPStoreLocatorSpider):
    name = "wiener_feinbacker_heberer_de"
    item_attributes = {
        "brand": "Wiener Feinbäcker Heberer",
        "brand_wikidata": "Q15854357",
        "extras": Categories.SHOP_BAKERY.value,
    }
    allowed_domains = ["heberer.de"]

    def parse_item(self, item, location):
        item.pop("addr_full", None)

        item["name"] = unescape(item["name"])
        if len(item["name"].split(" (")) > 1:
            old_name = item["name"]
            item["name"], located_in_tag = old_name.split(" (", 1)
            if re.search(r"\WRewe\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = REWEDESpider.item_attributes["brand"]
                item["located_in_wikidata"] = REWEDESpider.item_attributes["brand_wikidata"]
            elif re.search(r"\WHIT\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = HITDESpider.item_attributes["brand"]
                item["located_in_wikidata"] = HITDESpider.item_attributes["brand_wikidata"]
            elif re.search(r"\WKarstadt\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = GaleriaDESpider.item_attributes["brand"]
                item["located_in_wikidata"] = GaleriaDESpider.item_attributes["brand_wikidata"]
            elif re.search(r"\WKaufland\W", located_in_tag, flags=re.IGNORECASE):
                item["located_in"] = KauflandSpider.item_attributes["brand"]
                item["located_in_wikidata"] = KauflandSpider.item_attributes["brand_wikidata"]
            else:
                item["name"] = old_name

        hours_string = " ".join(
            filter(None, map(str.strip, Selector(text=location["description"]).xpath("//text()").getall()))
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_DE)

        yield item
