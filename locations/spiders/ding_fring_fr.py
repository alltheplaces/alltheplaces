import re
import unicodedata
from collections.abc import AsyncIterator
from typing import Any

from scrapy import FormRequest, Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class DingFringFRSpider(Spider):
    name = "ding_fring_fr"
    item_attributes = {
        "brand": "Ding Fring",
        "brand_wikidata": "Q141502105",
        "name": "Ding Fring",
        "operator": "Le Relais",
        "operator_wikidata": "Q16654240",
    }

    async def start(self) -> AsyncIterator[FormRequest]:
        # The map only returns points inside the posted bounding box; a world-sized one returns them all.
        yield FormRequest(
            url="https://siroco.lerelais.org/index.php?do=pointsdecollecte/ajax",
            formdata={
                "action": "getDing",
                "nomPA": "",
                "adressePA": "",
                "zoom": "5",
                "slat": "-85",
                "slng": "-180",
                "nlat": "85",
                "nlng": "180",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for point in response.json()["aappEtEmpPourCarte"]:
            if point["inactif"]:
                continue

            lines = [
                line.strip()
                for line in Selector(text=point["content"]).css(".lci_address::text").getall()
                if line.strip()
            ]
            match = re.match(r"(\d{5})\s+(.+)", lines[-1]) if lines else None
            postcode, commune = match.groups() if match else (None, "")

            item = Feature()
            item["ref"] = point["id"]
            item["lat"] = point["lat"]
            item["lon"] = point["lng"]
            item["street_address"] = lines[0] if len(lines) > 1 else None
            item["postcode"] = postcode
            item["city"] = commune.title() or None
            item["country"] = "FR"

            # Names look like "CITY - Ding Fring Suffix". The source drops accents, so when the name's
            # city is the commune, use the commune (accented) instead.
            name_city, _, name_rest = point["name"].partition(" - ")
            suffix = re.sub(r"^ding\s*fring\s*", "", name_rest, flags=re.I).strip()
            if self.fold(name_city) == self.fold(commune):
                name_city = commune
            item["branch"] = " ".join(filter(None, [name_city.title(), suffix]))

            apply_category(Categories.SHOP_CLOTHES, item)
            item["extras"]["second_hand"] = "only"

            yield item

    @staticmethod
    def fold(text: str) -> str:
        return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode())
