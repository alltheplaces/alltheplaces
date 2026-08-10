import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser

# Products listed in the "text" field -> OSM fuel tag.
FUELS = {
    "Puma Super": Fuel.OCTANE_95,
    "Max Premium": Fuel.OCTANE_98,
    "Puma Diesel": Fuel.DIESEL,
    "ION Puma Diesel": Fuel.DIESEL,
}


class PumaEnergyARSpider(Spider):
    name = "puma_energy_ar"
    item_attributes = {"brand": "Puma", "brand_wikidata": "Q7259769"}

    async def start(self) -> AsyncIterator[Request]:
        # get_stations is a Laravel endpoint that needs a CSRF token from the locator page.
        yield Request("https://pumaenergyarg.com.ar/encontra_tu_estacion", callback=self.parse_token)

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        # Empty filter arrays return the whole network; the arrays must be sent as JSON
        # (form encoding drops empty arrays and the endpoint then 500s).
        yield JsonRequest(
            url="https://pumaenergyarg.com.ar/get_stations",
            data={
                "_token": response.xpath('//meta[@name="csrf-token"]/@content').get(),
                "fuel_type": [],
                "shop_type": [],
                "franchise": [],
                "puma_pris": 0,
                "chargebox": 0,
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)  # maps id -> ref, lat/lon, address -> addr_full
            item.pop("name", None)  # API "name" is the street address (kept in addr_full); NSI supplies name=Puma

            apply_category(Categories.FUEL_STATION, item)
            if "24hs" in (location.get("schedule") or ""):
                item["opening_hours"] = "24/7"
            apply_yes_no(Fuel.CNG, item, location.get("fuel_type") in ("Dual", "GNC"))
            apply_yes_no(Fuel.ELECTRIC, item, location.get("chargebox") == "1")
            for product in re.split(r"<br\s*/?>", location.get("text") or ""):
                if fuel := FUELS.get(product.strip(" -").strip()):
                    apply_yes_no(fuel, item, True)

            yield item
