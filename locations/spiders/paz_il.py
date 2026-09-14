from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.react_server_components import parse_rsc


class PazILSpider(Spider):
    name = "paz_il"
    item_attributes = {"brand": "פז", "brand_wikidata": "Q2211731"}
    allowed_domains = ["www.paz.co.il"]
    start_urls = ["https://www.paz.co.il/service-locator"]
    requires_proxy = True  # Radware Bot Manager blocks direct requests.

    # metaData service label (Hebrew) -> tag.
    SERVICES = {
        "פז wash": Extras.CAR_WASH,  # Paz wash
        "כספומט": Extras.ATM,  # ATM
    }

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The service locator is a Next.js app; the stations are nested in the streamed RSC
        # flight payload (self.__next_f.push([1, "<chunk>"]) calls) with $-prefixed references.
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        chunks = [obj[1] for obj in map(chompjs.parse_js_object, scripts) if len(obj) > 1 and isinstance(obj[1], str)]
        data = dict(parse_rsc("".join(chunks).encode()))

        def resolve(value):
            # RSC references are "$<hex row id>"; other "$"-prefixed tokens (e.g. "$L1",
            # "$undefined", the escaped literal "$$") are left as-is.
            while isinstance(value, str) and len(value) > 1 and value[0] == "$" and value[1] != "$":
                ref = value[1:]
                if not all(c in "0123456789abcdefABCDEF" for c in ref) or (nxt := data.get(int(ref, 16))) is None:
                    break
                value = nxt
            return value

        for station in self.find_stations(data, resolve):
            # type 1 = fuel station; 2/7 = Paz-owned supermarkets, 10 = standalone EV charger.
            if station.get("type") != 1:
                continue

            item = DictParser.parse(station)  # id->ref, geoLocation->lat/lon, address->addr_full
            item["ref"] = str(item["ref"])
            item["branch"] = item.pop("name", None)  # brand name comes from NSI
            item["street_address"] = item.pop("addr_full", None)
            item.pop("state", None)  # "region" is a Paz marketing zone (incl. a city), not addr:state
            apply_category(Categories.FUEL_STATION, item)

            apply_yes_no(Fuel.OCTANE_98, item, station.get("product98"))
            apply_yes_no(Fuel.LPG, item, station.get("productGas"))  # גפ"מ autogas
            apply_yes_no(Fuel.ADBLUE, item, station.get("productUrea"))  # אוריאה
            apply_yes_no(Fuel.ELECTRIC, item, station.get("isElectric"))

            for service in station.get("metaData") or []:
                if tag := self.SERVICES.get(service.get("name")):
                    apply_yes_no(tag, item, True)

            yield item

    @classmethod
    def find_stations(cls, data: dict, resolve) -> list:
        # The station list sits deep in the RSC component tree; find it by shape (a list
        # whose items carry a geoLocation) rather than a brittle fixed key path.
        for value in data.values():
            if found := cls._find_list(resolve(value), resolve, 0):
                return found
        return []

    @classmethod
    def _find_list(cls, value: Any, resolve, depth: int) -> list | None:
        if depth > 40:
            return None
        value = resolve(value)
        if isinstance(value, list):
            if len(value) >= 20 and isinstance(first := resolve(value[0]), dict) and "geoLocation" in first:
                return [resolve(v) for v in value]
            for item in value:
                if found := cls._find_list(item, resolve, depth + 1):
                    return found
        elif isinstance(value, dict):
            for item in value.values():
                if found := cls._find_list(item, resolve, depth + 1):
                    return found
        return None
