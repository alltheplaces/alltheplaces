from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# Per-day opening-hours fields ("<day>Horarios") mapped to OSM day abbreviations.
HOURS_FIELDS = (
    ("lunes", "Mo"),
    ("martes", "Tu"),
    ("miercoles", "We"),
    ("jueves", "Th"),
    ("viernes", "Fr"),
    ("sabado", "Sa"),
    ("domingo", "Su"),
)


class AxionARSpider(Spider):
    name = "axion_ar"
    item_attributes = {"brand": "Axion", "brand_wikidata": "Q62131749"}

    async def start(self) -> AsyncIterator[Any]:
        # top=1000 returns every station in one page; the filter keeps only service stations (EESS).
        yield JsonRequest(
            url="https://www.axionenergy.com/wp-json/axion/v1/estaciones?top=1000&filters=Title%20eq%20%27EESS%27"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json()["items"]:
            item = DictParser.parse(poi)  # maps Direccion (-> addr_full), Telefono (-> phone)
            item.pop("name", None)  # DictParser sets this from "Title", which is just the type "EESS"
            item.pop("email", None)  # the source email field is malformed (duplicated)
            if (item.get("phone") or "").startswith("0800"):
                item.pop("phone")  # shared national call-centre line, not the branch's own number
            item["ref"] = poi["PBL"]
            item["branch"] = poi.get("NombreEESSAgro") or poi.get("RazonSocial")
            item["street_address"] = item.pop("addr_full", None)
            item["city"] = poi.get("Localidad")
            item["state"] = poi.get("Provincia")
            item["lat"], item["lon"] = self.parse_coordinates(poi.get("Latitud"), poi.get("Longitud"))
            item["opening_hours"] = self.parse_opening_hours(poi)
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.OCTANE_95, item, poi.get("AXIONSUPER") == "1")  # Axion Súper
            apply_yes_no(Fuel.OCTANE_98, item, poi.get("QUANTIUM") == "1")  # Quantium premium petrol
            apply_yes_no(Fuel.DIESEL, item, poi.get("AXIONDIESELX10") == "1" or poi.get("QUANTIUMDIESELX10") == "1")
            apply_yes_no(Fuel.CNG, item, poi.get("GNC") == "1")
            # NB: the on-site Spot!/AXION shop is deliberately NOT tagged shop=convenience.
            # That is a top-level category tag, and NSI only matches a brand when the item's
            # categories are a subset of the brand's; Axion's NSI entry is amenity=fuel only,
            # so adding shop=convenience breaks the brand match (name/nsi_id lost).
            apply_yes_no(
                Extras.FAST_FOOD, item, poi.get("ParadaSanguchera") == "1"
            )  # Parada Sanguchera sandwich counter
            apply_yes_no(Extras.CAR_REPAIR, item, poi.get("BoschCarService") == "1")
            apply_yes_no(Extras.OIL_CHANGE, item, poi.get("CastrolOilExpress") == "1")
            yield item

    @staticmethod
    def parse_opening_hours(poi: dict) -> OpeningHours:
        oh = OpeningHours()
        for field, day in HOURS_FIELDS:
            for time_range in (poi.get("{}Horarios".format(field)) or "").split(","):
                time_range = time_range.strip().replace(" ", "")
                if "-" not in time_range:
                    continue
                start, end = time_range.split("-", 1)
                if end == "24:00":  # OpeningHours parses %H:%M, which has no hour 24
                    end = "23:59"
                try:
                    oh.add_range(day, start, end)
                except ValueError:
                    pass
        return oh

    @staticmethod
    def parse_coordinates(latitude: str, longitude: str) -> tuple[float | None, float | None]:
        def to_float(value: str) -> float | None:
            value = (value or "").replace(",", ".")
            parts = value.split(".")
            if len(parts) > 2:  # a few coordinates carry a stray separator, e.g. "-33.624.167"
                value = "{}.{}".format(parts[0], "".join(parts[1:]))
            try:
                return float(value)
            except ValueError:
                return None

        lat, lon = to_float(latitude), to_float(longitude)
        if lat and lon and -56.0 < lat < -21.0 and -74.0 < lon < -53.0:
            return lat, lon
        return None, None
