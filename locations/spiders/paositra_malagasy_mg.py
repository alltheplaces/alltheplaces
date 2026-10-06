import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# "08h00mn à 12h00 min", "15h 00mn a 16h 30 min", "14 h 30 à 17h30mn", "08h à 11h"
TIME = r"(\d{1,2})\s*h\s*(\d{2})?\s*(?:mn|min(?:utes)?)?"
RANGE_RE = re.compile(TIME + r"\s*(?:à|a|-)\s*" + TIME, re.IGNORECASE)
DAYS_RE = re.compile(r"(lundi\s+au\s+vendredi|samedi)", re.IGNORECASE)
PHONE_RE = re.compile(r"T[ée]l[ée]phone\s*:\s*([\d ]{9,})")


class PaositraMalagasyMgSpider(Spider):
    name = "paositra_malagasy_mg"
    item_attributes = {"operator": "Paositra Malagasy", "operator_wikidata": "Q7132299"}
    # The "Nos agences" page (https://paositramalagasy.mg/nos_agence) embeds this uMap, one layer
    # per former province; uMap exports the whole map, all layers included, as one GeoJSON-like file.
    start_urls = ["https://umap.openstreetmap.fr/map/573038/download/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for layer in response.json()["layers"]:
            province = layer.get("_umap_options", {}).get("name")
            for feature in layer["features"]:
                properties = feature["properties"]
                item = Feature()
                item["ref"] = feature["id"]
                item["branch"] = re.sub(r"^Agence\s+", "", properties["name"].strip(), flags=re.IGNORECASE)
                item["lon"], item["lat"] = feature["geometry"]["coordinates"][:2]
                item["state"] = province.title() if province else None
                description = properties.get("description") or ""
                if phone := PHONE_RE.search(description):
                    item["phone"] = phone.group(1).strip()
                item["opening_hours"] = self.parse_hours(description)
                item["country"] = "MG"
                if item["branch"].lower().startswith("centre de tri"):
                    apply_category(Categories.POST_DEPOT, item)  # national sorting centre (CTPR), no counter
                else:
                    apply_category(Categories.POST_OFFICE, item)
                yield item

    @staticmethod
    def parse_hours(description: str) -> OpeningHours | None:
        # Day labels are followed by one or two time ranges, on the same line or the next ones.
        oh = OpeningHours()
        days = None
        position = 0
        for match in DAYS_RE.finditer(description):
            if days is not None:
                PaositraMalagasyMgSpider.add_ranges(oh, days, description[position : match.start()])
            days = DAYS[:5] if match.group(1).lower().startswith("lundi") else ["Sa"]
            position = match.end()
        if days is None:
            return None
        PaositraMalagasyMgSpider.add_ranges(oh, days, description[position:])
        return oh

    @staticmethod
    def add_ranges(oh: OpeningHours, days: list[str], text: str) -> None:
        for h1, m1, h2, m2 in RANGE_RE.findall(text):
            oh.add_days_range(days, "{}:{}".format(h1, m1 or "00"), "{}:{}".format(h2, m2 or "00"))
