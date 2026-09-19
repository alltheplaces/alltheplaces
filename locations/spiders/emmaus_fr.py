import re
from typing import Any
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# "Le Relais" (Q16654240) is a separate cooperative brand (Ding Fring, Label Fripe,
# Friperie le Léopard, "Le Relais, La Boutique") that shares this same feed with Emmaüs
# but never brands its own shops as "Emmaüs". Identified by domain, not by name, since
# its regional retail names vary and none of them contain "relais"/"dingfring".
RELAIS_URL_DOMAINS = {
    "lerelais.org",
    "www.lerelais.org",
    "lerelaislaboutique.com",
    "www.lerelaislaboutique.com",
    "relaisest.org",
    "www.relaisest.org",
    "dingfring-nordest-iledefrance.fr",
    "www.dingfring-nordest-iledefrance.fr",
    "labelfripe.fr",
    "www.labelfripe.fr",
    "lerelais-soissons.org",
    "www.lerelais-soissons.org",
    "le-relais-bretagne.business.site",
    "dingfringlaval.business.site",
}
RELAIS_EMAIL_DOMAINS = {"lerelais.org", "relaisest.org", "dingfring-nordest-iledefrance.fr"}


class EmmausFRSpider(Spider):
    name = "emmaus_fr"
    item_attributes = {
        "brand": "Mouvement Emmaüs",
        "brand_wikidata": "Q989437",
        "name": "Emmaüs",
        "operator": "Emmaüs France",
        "operator_wikidata": "Q3053001",
    }
    start_urls = ["https://www.emmaus-france.org/boutiquesjson.php"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["listsrcfull"]:
            if store.get("acheter") != "1":
                continue

            url_domain = urlparse(store.get("url") or "").netloc.lower()
            email_domain = (store.get("email") or "").rsplit("@", 1)[-1].lower()
            if url_domain in RELAIS_URL_DOMAINS or email_domain in RELAIS_EMAIL_DOMAINS:
                continue
            if not re.search(r"emma.s", store.get("title") or "", re.I):
                self.crawler.stats.inc_value("atp/emmaus_fr/unclassified_entry")
                self.logger.warning("Neither a known Le Relais domain nor 'Emmaüs' in title: %s", store.get("title"))

            item = Feature()
            item["ref"] = store["ID"]
            item["branch"] = store["title"]
            gps_parts = (store.get("gps") or "").split(",")
            if len(gps_parts) >= 2:
                item["lat"], item["lon"] = gps_parts[0], gps_parts[1]
            item["street_address"], item["postcode"], item["city"] = self.parse_address(store)
            item["country"] = "FR"
            item["phone"] = store.get("telephone")
            item["email"] = store.get("email")
            item["website"] = store.get("permalink")
            item["facebook"] = store.get("facebook")
            item["opening_hours"] = self.parse_hours(store)

            apply_category(Categories.SHOP_CHARITY, item)

            yield item

    def parse_address(self, store: dict) -> tuple[str | None, str | None, str | None]:
        address = store.get("adresse") or ""
        if match := re.search(r"(\d{5})\s+([^\d,]+)$", address):
            return address[: match.start()].rstrip(" ,–—-") or None, match.group(1), match.group(2).strip()
        if match := re.search(r"(\d{4})\s+([^\d,]+)$", address):
            return address[: match.start()].rstrip(" ,–—-") or None, "0" + match.group(1), match.group(2).strip()
        if match := re.search(r"\b(\d{5})\b", store.get("adresse2") or ""):
            return address or None, match.group(1), None
        return address or None, None, None

    def parse_hours(self, store: dict) -> OpeningHours:
        oh = OpeningHours()
        for day_index, day in enumerate(DAYS, start=1):
            am_begin = self.parse_time(store.get(f"h_{day_index}_am_begin"))
            am_end = self.parse_time(store.get(f"h_{day_index}_am_end"))
            pm_begin = self.parse_time(store.get(f"h_{day_index}_pm_begin"))
            pm_end = self.parse_time(store.get(f"h_{day_index}_pm_end"))
            if am_begin and am_end:
                oh.add_range(day, am_begin, am_end)
            if pm_begin and pm_end:
                oh.add_range(day, pm_begin, pm_end)
            # One continuous span is given as am_begin + pm_end with both middle fields empty.
            if am_begin and pm_end and not am_end and not pm_begin:
                oh.add_range(day, am_begin, pm_end)
        return oh

    @staticmethod
    def parse_time(value: str | None) -> str | None:
        # A handful of records use "18h30" instead of "18:30"; a few others are
        # outright malformed (e.g. "1700", "17:0") and are dropped rather than guessed at.
        if value and (match := re.fullmatch(r"(\d{1,2})[h:](\d{2})", value)):
            return f"{match.group(1)}:{match.group(2)}"
        return None
