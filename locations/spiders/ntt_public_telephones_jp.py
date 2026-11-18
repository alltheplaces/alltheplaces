from typing import Any, AsyncIterator, Iterable

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

# Tokyo (EPSG:4301) -> WGS 84 (EPSG:4326) via EPSG:15484 (Tokyo to WGS 84 (108)), the same
# parameters the map's own JavaScript uses for the reverse conversion.
TOKYO_TO_WGS84 = Transformer.from_pipeline("EPSG:15484")

NTT_EAST = {
    "operator": "東日本電信電話株式会社",
    "operator_wikidata": "Q11527212",
    "base_url": "https://publictelephone.ntt-east.co.jp/ptd/map/",
}
NTT_WEST = {
    "operator": "西日本電信電話株式会社",
    "operator_wikidata": "Q11628418",
    "base_url": "https://www.ntt-west.co.jp/ptd/map/",
}

# Marker icons: outdoor/indoor, and whether the telephone is usable at all hours.
# Icon 5 is wheelchair accessible, with hours that are not given.
ICONS = {
    "1": {"indoor": False, "24/7": True},
    "2": {"indoor": True, "24/7": True},
    "3": {"indoor": False, "24/7": False},
    "4": {"indoor": True, "24/7": False},
    "5": {"wheelchair": True},
}


class NttPublicTelephonesJPSpider(Spider):
    name = "ntt_public_telephones_jp"

    # The API returns at most 30 telephones in a bounding box, with no pagination.
    MAX_RESULTS = 30
    # Bounding boxes are in milliseconds of arc in the Tokyo datum: left, bottom, right, top.
    # Each company only returns its own area, so both are asked for the whole of Japan.
    JAPAN_BOUNDS = (122 * 3600000, 20 * 3600000, 154 * 3600000, 46 * 3600000)
    # About 30m. Several telephones in one building are already merged into a single marker.
    MIN_CELL_SIZE = 1000

    async def start(self) -> AsyncIterator[JsonRequest]:
        for operator in (NTT_EAST, NTT_WEST):
            yield self.make_request(operator, self.JAPAN_BOUNDS)

    def make_request(self, operator: dict, bounds: tuple[int, int, int, int]) -> JsonRequest:
        left, bottom, right, top = bounds
        return JsonRequest(
            f"{operator['base_url']}gettelephones?left={left}&bottom={bottom}&right={right}&top={top}",
            cb_kwargs={"operator": operator, "bounds": bounds},
        )

    def parse(self, response: Response, operator: dict, bounds: tuple[int, int, int, int]) -> Iterable[Any]:
        telephones = response.json()
        left, bottom, right, top = bounds
        if len(telephones) >= self.MAX_RESULTS:
            if right - left > self.MIN_CELL_SIZE or top - bottom > self.MIN_CELL_SIZE:
                x, y = (left + right) // 2, (bottom + top) // 2
                for child in ((left, bottom, x, y), (x, bottom, right, y), (left, y, x, top), (x, y, right, top)):
                    yield self.make_request(operator, child)
                return
            self.logger.warning(f"Results may be truncated in {bounds}")
            self.crawler.stats.inc_value(f"atp/{self.name}/truncated_cell")

        for telephone in telephones:
            # Neighbouring cells share edges, so keep only telephones on this cell's lower and left edges.
            if left <= telephone["x"] < right and bottom <= telephone["y"] < top:
                yield self.parse_telephone(telephone, operator)

    def parse_telephone(self, telephone: dict, operator: dict) -> Feature:
        item = Feature()
        # The map's detail page for a telephone is addressed by its coordinates.
        item["ref"] = "{}_{}".format(telephone["y"], telephone["x"])
        item["website"] = "{}guidemap/{}".format(operator["base_url"], item["ref"])
        item["lat"], item["lon"] = TOKYO_TO_WGS84.transform(telephone["y"] / 3600000, telephone["x"] / 3600000)
        item["operator"] = operator["operator"]
        item["operator_wikidata"] = operator["operator_wikidata"]
        apply_category(Categories.TELEPHONE, item)

        if icon := ICONS.get(telephone["icon"]):
            if "indoor" in icon:
                apply_yes_no("indoor", item, icon["indoor"], False)
            if icon.get("24/7"):
                item["opening_hours"] = "24/7"
            if icon.get("wheelchair"):
                apply_yes_no(Extras.WHEELCHAIR, item, True)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_icon/{telephone['icon']}")
        return item
