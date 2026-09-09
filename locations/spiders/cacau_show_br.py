from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.items import Feature

BASE_URL = "https://www.cacaushow.com.br/on/demandware.store/Sites-CacauShow-Site/pt_BR/Stores-FindStores"

# The Stores-FindStores endpoint always returns only the (up to) 50 stores
# nearest to the queried point, regardless of the radius requested, and the
# search behaves as a real (roughly city-block scale) distance cutoff rather
# than a simple "nearest 50 nationally" ranking (a query in the middle of
# the Amazon rainforest returns zero results). So a query that returns the
# cap means there may be additional stores just outside of its result set,
# and neighbouring points must be queried too to find them.
RESULT_CAP = 50

# Grid spacing, in degrees, between query points, chosen to be smaller than
# the store locator's effective search radius (empirically, two points
# ~0.15 degrees apart in central São Paulo returned completely disjoint
# sets of 50 stores) so that flood-filling outward from a "capped" query
# point reliably finds any stores just outside its result set.
GRID_STEP = 0.1

# Safety limit on the number of distinct grid cells queried, to bound
# runaway flood-fill expansion in the unlikely event a large area
# continuously returns capped results.
MAX_QUERIES = 20_000


class CacauShowBRSpider(Spider):
    name = "cacau_show_br"
    item_attributes = {"brand": "Cacau Show", "brand_wikidata": "Q9671713", "name": "Cacau Show"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawled_refs: set[str] = set()
        self.visited_cells: set[tuple[int, int]] = set()

    async def start(self) -> AsyncIterator[Request]:
        for city in city_locations("BR", 0):
            for request in self.request_point(city["latitude"], city["longitude"]):
                yield request

    def request_point(self, lat: float, lon: float) -> Iterable[Request]:
        cell = (round(lat / GRID_STEP), round(lon / GRID_STEP))
        if cell in self.visited_cells or len(self.visited_cells) >= MAX_QUERIES:
            return
        self.visited_cells.add(cell)

        snapped_lat, snapped_lon = cell[0] * GRID_STEP, cell[1] * GRID_STEP
        url = f"{BASE_URL}?showMap=true&lat={snapped_lat}&long={snapped_lon}"
        yield Request(url, callback=self.parse, cb_kwargs={"lat": snapped_lat, "lon": snapped_lon})

    def parse(self, response: Response, lat: float, lon: float) -> Iterable[Feature | Request]:
        stores = response.json().get("stores") or []

        for store in stores:
            if store.get("isTransferStore"):
                continue

            ref = str(store.get("ID"))
            if not ref or ref in self.crawled_refs:
                continue
            self.crawled_refs.add(ref)

            item = DictParser.parse(store)
            item["ref"] = ref
            item["branch"] = item.pop("name", None)
            item["country"] = "BR"

            address_parts = [p for p in (store.get("address1"), store.get("address2")) if p]
            item["street_address"] = ", ".join(address_parts) if address_parts else None

            apply_category(Categories.SHOP_CHOCOLATE, item)

            yield item

        if len(stores) >= RESULT_CAP:
            for d_lat, d_lon in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                yield from self.request_point(lat + d_lat * GRID_STEP, lon + d_lon * GRID_STEP)
