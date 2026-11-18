import json
import re
from datetime import datetime
from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

POP_UP = re.compile(r"pop[- ]?up|[ée]ph[ée]m[èe]re|ef[íi]mer", re.IGNORECASE)


class CacheCacheSpider(JSONBlobSpider):
    name = "cache_cache"
    item_attributes = {"brand": "Cache Cache", "brand_wikidata": "Q63064086", "name": "Cache Cache"}
    start_urls = [
        "https://www.cache-cache.fr/on/demandware.store/Sites-CCH_FR_SFRA-Site/fr_FR/Stores-FindStores?lat=46.6&long=2.4&radius=20000&showMap=false"
    ]
    # Cloudflare challenges plain requests, and Camoufox from CI IPs.
    requires_proxy = "FR"
    custom_settings = {
        # robots.txt disallows /on/demandware.store/.
        "ROBOTSTXT_OBEY": False,
        "ZYTE_API_SKIP_HEADERS": ["Cookie", "User-Agent"],
    }

    def extract_json(self, response: TextResponse) -> list[dict]:
        data = response.json()
        cards = Selector(text=data["storesResultsHtml"]).css(".card-body[id]")
        self.websites = {card.attrib["id"]: card.css(".storelocator-link::attr(href)").get() for card in cards}
        return data["stores"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        custom = feature.get("custom") or {}
        # The locator also lists multi-brand Vib's shops.
        if custom.get("BMNR_libBrand") != "CACHE CACHE":
            return
        if POP_UP.search(
            " ".join(filter(None, [feature.get("name"), feature.get("address1"), feature.get("address2")]))
        ):
            self.logger.info(f"Skipping pop-up store {item['ref']}: {feature.get('name')}")
            return

        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        website = self.websites.get(item["ref"])
        if not item.get("phone") or not re.search(r"/magasins-[^/]+-\d+\.html$", website or ""):
            # Pop-ups seen so far have neither a phone nor a regular store page.
            self.logger.warning(f"Store {item['ref']} ({item['branch']}) lacks a phone or store page")
        # Spanish store pages are empty (their Stores-Detail include returns HTTP 500).
        if item.get("country") == "ES":
            item["branch"] = re.sub(r"\s*-\s*ES$", "", item["branch"] or "")
        else:
            item["website"] = website
        if closing_date := custom.get("BMNR_dateFermetureDefinitive"):
            set_closed(item, datetime.strptime(closing_date, "%d%m%Y"))

        oh = OpeningHours()
        for day, hours in json.loads(custom.get("BMNR_horaires") or "{}").items():
            if not (day := sanitise_day(day, DAYS_FR)):
                continue
            # Days without a lunch break only fill ouverture_matin and fermeture_apresmidi.
            if hours.get("fermeture_matin") or hours.get("ouverture_apresmidi"):
                oh.add_range(day, hours.get("ouverture_matin"), hours.get("fermeture_matin"), "%H%M")
                oh.add_range(day, hours.get("ouverture_apresmidi"), hours.get("fermeture_apresmidi"), "%H%M")
            else:
                oh.add_range(day, hours.get("ouverture_matin"), hours.get("fermeture_apresmidi"), "%H%M")
        item["opening_hours"] = oh

        # NSI's Cache Cache entry doesn't cover Spain.
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
