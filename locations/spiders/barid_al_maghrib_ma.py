import math
import re
from typing import Any, AsyncIterator

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature

# AllStoresR returns every outlet within 15 km of the point. A triangular lattice with 22 km spacing
# covers the plane with 12.7 km circles, leaving margin for the lattice shearing over long distances.
GRID_SPACING_KM = 22
ISEADGG_RADIUS_KM = 24


class BaridAlMaghribMASpider(Spider):
    """
    Post offices of Barid Al-Maghrib (Poste Maroc), from the agency finder on barid.ma.

    The finder lists three kinds of outlet:
      - "ABB": the post office network (counters run by Al Barid Bank, Barid Al-Maghrib's subsidiary)
      - "BC": Barid Cash money transfer outlets (not post offices; skipped)
      - "BAM": mail sorting/distribution centres and Amana parcel counters
    """

    name = "barid_al_maghrib_ma"
    item_attributes = {"operator": "Poste Maroc بريد المغرب", "operator_wikidata": "Q3399778"}
    allowed_domains = ["www.barid.ma"]

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in self.search_points():
            yield Request(
                "https://www.barid.ma/bamb2cstorefront/fr/store-finder/AllStoresR?latitude={:.4f}&longitude={:.4f}".format(
                    lat, lon
                )
            )

    @staticmethod
    def search_points() -> list[tuple[float, float]]:
        # The 24 km ISEADGG centroids leave gaps with a 15 km search radius, so lay a finer lattice over
        # the area they cover (Morocco and Western Sahara, where Barid Al-Maghrib operates). Lattice
        # points up to 24 + 14 km from a centroid are kept so that coastal and border towns are covered.
        centroids = country_iseadgg_centroids(["MA", "EH"], ISEADGG_RADIUS_KM)
        keep_km = ISEADGG_RADIUS_KM + 14
        min_lat, max_lat = min(c[0] for c in centroids) - 0.4, max(c[0] for c in centroids) + 0.4
        min_lon, max_lon = min(c[1] for c in centroids) - 0.5, max(c[1] for c in centroids) + 0.5
        mid_lon = (min_lon + max_lon) / 2
        columns = int(111.32 * (max_lon - min_lon) / GRID_SPACING_KM / 2) + 1
        points = []
        lat, row = min_lat, 0
        while lat < max_lat:
            km_per_degree = 111.32 * math.cos(math.radians(lat))
            for column in range(-columns, columns + 1):
                lon = mid_lon + (column + (0.5 if row % 2 else 0)) * GRID_SPACING_KM / km_per_degree
                if not min_lon < lon < max_lon:
                    continue
                if any(abs(lat - c[0]) < 0.4 and BaridAlMaghribMASpider.km(lat, lon, *c) <= keep_km for c in centroids):
                    points.append((lat, lon))
            lat += GRID_SPACING_KM * math.sqrt(3) / 2 / 110.57
            row += 1
        return points

    @staticmethod
    def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        x = (lon2 - lon1) * 111.32 * math.cos(math.radians((lat1 + lat2) / 2))
        y = (lat2 - lat1) * 110.57
        return math.hypot(x, y)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not response.text.lstrip().startswith("{"):
            return  # no outlet within the search radius: the finder returns its HTML page instead
        for store in chompjs.parse_js_object(response.text)["data"]:
            kind = store["agenceType"]
            if kind == "BC":
                continue  # Barid Cash money transfer outlet
            name = store["displayName"].strip()
            if kind == "BAM" and "MESSAGERIE" not in name:
                continue  # sorting/distribution centre, no public counter

            item = Feature()
            item["ref"] = store["name"]
            item["branch"] = name
            item["lat"], item["lon"] = store["latitude"], store["longitude"]
            item["street_address"] = " ".join(filter(None, [store["line1"], store["line2"]])).strip()
            item["city"] = store["town"]
            item["postcode"] = store["postalCode"]
            item["phone"] = store["phone"]
            item["opening_hours"] = self.parse_hours(store.get("openings") or {})
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(openings: dict) -> OpeningHours:
        # {"lun.": "08:00 - 16:30", ..., "dim.": "Fermé"}
        oh = OpeningHours()
        for day, hours in openings.items():
            day = DAYS_FR.get(day.strip(". ").title())
            if not day:
                continue
            ranges = re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", hours or "")
            if ranges:
                for start, end in ranges:
                    oh.add_range(day, start, end)
            else:
                oh.set_closed(day)
        return oh
