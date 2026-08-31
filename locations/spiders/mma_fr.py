import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature

HOURS_RE = re.compile(r"(\d{1,2})\s*h\s*(\d{2})\s*-\s*(\d{1,2})\s*h\s*(\d{2})")


class MmaFRSpider(Spider):
    name = "mma_fr"
    item_attributes = {"brand": "MMA", "brand_wikidata": "Q3331046"}
    allowed_domains = ["agence.mma.fr"]

    # The "search-pdv" endpoint returns every agency within roughly 130 km of the
    # query point (it ignores any radius/limit larger than that), so a coarse
    # grid with plenty of overlap covers the whole country; dedupe on idPdv.
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.seen: set[str] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations("eu_centroids_80km_radius_country.csv", "FR"):
            yield JsonRequest(
                f"https://agence.mma.fr/modules/sag-composants-api/search-pdv"
                f"?latitude={lat}&longitude={lon}&limit=5000"
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for pdv in response.json():
            if pdv["idPdv"] in self.seen:
                continue
            self.seen.add(pdv["idPdv"])

            item = Feature()
            item["ref"] = pdv["idPdv"]
            item["branch"] = pdv["nom"].title()
            item["street_address"] = (pdv.get("voie") or "").title() or None
            # "commune" often carries a postal "CEDEX[ N]" routing suffix.
            item["city"] = (
                re.sub(r"\s+CEDEX(\s+\d+)?\s*$", "", pdv.get("commune") or "", flags=re.IGNORECASE).title() or None
            )
            item["postcode"] = pdv.get("codePostal")
            item["lat"] = pdv["latitude"]
            item["lon"] = pdv["longitude"]
            item["phone"] = pdv.get("numeroTel")
            item["email"] = pdv.get("emailDefaut")
            item["website"] = pdv.get("urlSite")
            # codePays in the feed is unreliable (stray "TH", "MC" on French
            # agencies); the network is metropolitan France plus Monaco (98000).
            item["country"] = "MC" if item["postcode"] == "98000" else "FR"
            item["opening_hours"] = self.parse_hours(pdv.get("horaires") or {})

            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item

    @staticmethod
    def parse_hours(horaires: dict) -> OpeningHours | None:
        oh = OpeningHours()
        for day_fr, rules in horaires.items():
            if not (day := sanitise_day(day_fr, DAYS_FR)):
                continue
            if rules.get("ferme"):
                oh.set_closed(day)
                continue
            # "sur RDV" / "Fermée" slots simply don't match and are skipped.
            for slot in (rules.get("matin"), rules.get("apresMidi"), rules.get("horairesJourneeContinue")):
                if slot and (m := HOURS_RE.search(slot)):
                    oh.add_range(day, f"{int(m[1]):02d}:{m[2]}", f"{int(m[3]):02d}:{m[4]}")
        return oh or None
