import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_IT
from locations.items import Feature

# e.g. "LUN - VEN alle 12:00", "LUN, MER, VEN alle 10:00", "MAR, GIO alle 10:00"
COLLECTION_TIME = re.compile(r"^(?P<days>[A-Z ,\-]+?)\s+alle\s+(?P<hour>\d{1,2})[:.](?P<minute>\d{2})$")


class PosteItalianePostboxesITSpider(Spider):
    """
    Letter boxes ("cassette postali") from the Poste Italiane map at https://www.poste.it/cerca/index.html
    (which redirects to the map app at https://www.poste.it/prenotazione/vieni-in-poste?tipologia=CassettePostali).

    The map API has two endpoints for a bounding box (centre plus half-spans in degrees):
      - geoSearch returns every location in the box, but groups close ones into clusters that only carry a count;
      - geoList returns full details for at most 20 locations, with offset pagination in no stable order.
    So boxes are split until geoSearch reports no clusters or geoList returns less than a full page.

    The older GeoCMS box finder (geocms.it, project "CassettePostali") still answers, but poste.it no longer links
    to it; it lists about 42,700 boxes against the current map's 25,500, and lacks ~1,700 of the current ones,
    so it appears to be an outdated copy that still includes removed boxes.
    """

    name = "poste_italiane_postboxes_it"
    item_attributes = {"operator": "Poste Italiane", "operator_wikidata": "Q495026"}
    custom_settings = {"CONCURRENT_REQUESTS_PER_DOMAIN": 1, "DOWNLOAD_DELAY": 1.25, "RETRY_TIMES": 10}

    API = "https://mapcollection.poste.it/v3/map/"
    LIST_LIMIT = 20
    # lat, lon, lat half-span, lon half-span; covers Italy, San Marino and Vatican City.
    ITALY = (41.25, 12.6, 5.85, 6.0)
    # About 50m; a box this small still holding more than LIST_LIMIT locations is paged through instead.
    MIN_HALF_SPAN = 0.0005

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.search_request(*self.ITALY)

    def make_body(self, lat: float, lon: float, half_lat: float, half_lon: float) -> dict:
        return {"lat": lat, "lon": lon, "spanLat": half_lat, "spanLon": half_lon, "tipoPunto": ["CassettaPostale"]}

    def search_request(self, lat: float, lon: float, half_lat: float, half_lon: float) -> JsonRequest:
        return JsonRequest(
            self.API + "geoSearch",
            data=self.make_body(lat, lon, half_lat, half_lon),
            callback=self.parse_search,
            cb_kwargs={"cell": (lat, lon, half_lat, half_lon)},
            dont_filter=True,
        )

    def list_request(
        self, cell: tuple[float, float, float, float], count: int | None = None, paged: bool = False, offset: int = 0
    ) -> JsonRequest:
        """List a cell; count is the number of boxes geoSearch reported for it, if known."""
        return JsonRequest(
            self.API + "geoList",
            data=self.make_body(*cell) | {"limit": self.LIST_LIMIT, "offset": offset},
            callback=self.parse_list,
            cb_kwargs={"cell": cell, "count": count, "paged": paged, "offset": offset},
            # A cell listed on an estimate may be listed again once geoSearch has counted it.
            dont_filter=True,
        )

    def parse_search(self, response: Response, cell: tuple[float, float, float, float]) -> Iterable[Any]:
        data = response.json()["data"]
        clusters = data.get("listaCluster") or []
        points = data.get("listaPunti") or []

        if not clusters:
            yield from self.parse_points(points)
            return

        count = len(points) + sum(int(cluster["numeroPuntiTotale"]) for cluster in clusters)
        if count <= self.LIST_LIMIT:
            yield self.list_request(cell, count)
            return

        if cell[2] <= self.MIN_HALF_SPAN:
            self.logger.warning(f"{count} boxes within {cell}, paging through them")
            self.crawler.stats.inc_value("atp/poste_italiane_postboxes_it/paged_cell")
            yield self.list_request(cell, count, paged=True)
            return

        # Estimate each quadrant's count from cluster centres; a quadrant expected to be small is listed directly,
        # and parse_list falls back to geoSearch if it turns out to hold a full page.
        estimates = {quadrant: 0 for quadrant in self.quadrants(cell)}
        for place in points + clusters:
            quadrant = self.quadrant_of(cell, float(place["lat"]), float(place["lon"]))
            estimates[quadrant] += int(place.get("numeroPuntiTotale", 1))
        for quadrant, estimate in estimates.items():
            if estimate <= self.LIST_LIMIT * 3 // 4:
                yield self.list_request(quadrant)
            else:
                yield self.search_request(*quadrant)

    @staticmethod
    def quadrants(cell: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
        lat, lon, half_lat, half_lon = cell
        return [
            (lat + d_lat, lon + d_lon, half_lat / 2, half_lon / 2)
            for d_lat in (-half_lat / 2, half_lat / 2)
            for d_lon in (-half_lon / 2, half_lon / 2)
        ]

    def quadrant_of(self, cell: tuple[float, float, float, float], lat: float, lon: float) -> tuple:
        return self.quadrants(cell)[(2 if lat >= cell[0] else 0) + (1 if lon >= cell[1] else 0)]

    def parse_list(
        self, response: Response, cell: tuple[float, float, float, float], count: int | None, paged: bool, offset: int
    ) -> Iterable[Any]:
        points = response.json()["data"].get("listaPunti") or []
        if len(points) < self.LIST_LIMIT or (count is not None and offset + len(points) >= count):
            yield from self.parse_points(points)
        elif paged:
            yield from self.parse_points(points)
            yield self.list_request(cell, count, paged=True, offset=offset + self.LIST_LIMIT)
        else:
            # A full page may be truncated, so count the cell first.
            self.crawler.stats.inc_value("atp/poste_italiane_postboxes_it/full_list_page")
            yield from self.parse_points(points)
            yield self.search_request(*cell)

    def parse_points(self, points: list[dict]) -> Iterable[Feature]:
        for point in points:
            if point.get("tipoPunto") != "CassettaPostale":
                continue
            yield self.parse_box(point)

    def parse_box(self, point: dict) -> Feature:
        item = Feature()
        item["ref"] = point["nomePunto"]
        item["lat"] = point["lat"]
        item["lon"] = point["lon"]
        item["street_address"] = point.get("indirizzoPunto")
        item["city"] = point.get("citta")
        item["postcode"] = point.get("cap")
        if province := point.get("provincia"):
            item["extras"]["addr:province"] = province
        if raw := point.get("orarioVuotatura"):
            if collection_times := self.parse_collection_times(raw):
                item["extras"]["collection_times"] = collection_times
            else:
                self.logger.warning(f"Unparsed collection time: {raw}")
                self.crawler.stats.inc_value("atp/poste_italiane_postboxes_it/unparsed_collection_time")
        apply_category(Categories.POST_BOX, item)
        return item

    @staticmethod
    def parse_collection_times(raw: str) -> str | None:
        match = COLLECTION_TIME.match(raw.strip())
        if not match:
            return None
        days = set()
        for part in match.group("days").split(","):
            ends = [DAYS_IT.get(end.strip().title()) for end in part.split("-")]
            if not all(ends) or len(ends) > 2:
                return None
            start, end = DAYS.index(ends[0]), DAYS.index(ends[-1])
            if end < start:
                return None
            days.update(DAYS[start : end + 1])
        return f"{format_days(days)} {int(match.group('hour')):02d}:{match.group('minute')}"


def format_days(days: set[str]) -> str:
    """Format a set of weekdays as OSM day ranges, e.g. {Mo, Tu, We, Fr} -> "Mo-We,Fr"."""
    indexes = sorted(DAYS.index(day) for day in days)
    runs = []
    for index in indexes:
        if runs and index == runs[-1][1] + 1:
            runs[-1][1] = index
        else:
            runs.append([index, index])
    parts = []
    for start, end in runs:
        if end - start >= 2:
            parts.append(f"{DAYS[start]}-{DAYS[end]}")
        else:
            parts.extend(DAYS[start : end + 1])
    return ",".join(parts)
