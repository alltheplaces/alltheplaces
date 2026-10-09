import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature

# "08h00mn", "12h00 min", "15h 00mn", "14 h 30", "08h"
TIME_RE = re.compile(r"(\d{1,2})\s*h(?:\s*(\d{2}))?(?:\s*(?:mn|min(?:utes)?)\b)?", re.IGNORECASE)
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
                if item["branch"].lower().startswith("centre de tri"):
                    apply_category(Categories.POST_DEPOT, item)  # national sorting centre (CTPR), no counter
                else:
                    apply_category(Categories.POST_OFFICE, item)
                yield item

    @staticmethod
    def parse_hours(description: str) -> OpeningHours:
        # "LUNDI au VENDREDI : 08h à 12h00 min / 14h a 17h min\nSamedi : 08h à 11h00 min"
        text = TIME_RE.sub(lambda m: "{}:{}".format(m.group(1), m.group(2) or "00"), description)
        text = re.sub(r"(?<=\d)\s+a\s+(?=\d)", " à ", text)
        oh = OpeningHours()
        oh.add_ranges_from_string(text, days=DAYS_FR, delimiters=DELIMITERS_FR)
        return oh
