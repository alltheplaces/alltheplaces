import re
import unicodedata
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature


class LaPlateformeDuBatimentFRSpider(Spider):
    name = "la_plateforme_du_batiment_fr"
    item_attributes = {
        "brand": "La Plateforme du Bâtiment",
        "brand_wikidata": "Q137972122",
        "name": "La Plateforme du Bâtiment",
    }
    allowed_domains = ["www.laplateforme.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The depot list endpoint needs a login, the per depot one does not.
        # Depot ids are small sequential numbers (1 to 75 in 2026).
        for uid in range(1, 151):
            yield JsonRequest(f"https://www.laplateforme.com/depot/json/detailed/{uid}")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        store = response.json()
        if store.get("status") != "ENABLED" or not store.get("is_enabled") or store["soon"]["enabled"]:
            return
        if store["without_products"]["enabled"]:
            # La Matériauthèque showrooms, by appointment and without stock
            return

        item = Feature()
        item["ref"] = str(store["uid"])
        item["branch"] = " ".join(store["label"].split())
        item["street_address"] = store["address"]
        item["postcode"] = store["zip_code"].zfill(5)
        item["city"] = store["city"]
        item["lat"] = store["latitude"]
        item["lon"] = store["longitude"]
        item["website"] = "https://www.laplateforme.com/depot/details/{}/{}".format(
            store["uid"], self.slugify(store["label"])
        )

        for phone in store["phone_numbers"]:
            if phone["label"] == "Accueil":
                item["phone"] = phone["value"]
            elif phone["label"] == "Fax":
                item["extras"]["fax"] = phone["value"]

        if hours := store.get("opening_hours"):
            item["opening_hours"] = OpeningHours()
            hours = re.sub(r"(\d{1,2})h(\d{2})?", lambda m: "{}:{}".format(m[1], m[2] or "00"), hours)
            item["opening_hours"].add_ranges_from_string(
                hours, days=DAYS_FR, delimiters=DELIMITERS_FR, closed=CLOSED_FR
            )

        apply_category(Categories.SHOP_TRADE, item)
        apply_category(Categories.TRADE_BUILDING_SUPPLIES, item)
        yield item

    @staticmethod
    def slugify(label: str) -> str:
        label = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
