import json
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class AzpetrolAZSpider(Spider):
    name = "azpetrol_az"
    item_attributes = {"brand": "Azpetrol", "brand_wikidata": "Q4034661"}

    async def start(self) -> AsyncIterator[Any]:
        # The unprefixed locale is Azeri. The "RSC" header returns the Next.js flight payload
        # (text/x-component) carrying the station JSON, instead of the fully rendered HTML page.
        yield Request(url="https://azpetrol.az/service-network", headers={"RSC": "1"})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Stations are embedded in the flight payload as a Strapi collection under locations.content.data.
        marker = '"locations":{"content":{"data":'
        if (start := response.text.find(marker)) == -1:
            self.logger.error("Azpetrol station data not found")
            return
        stations, _ = json.JSONDecoder().raw_decode(response.text[start + len(marker) :])

        for station in stations:
            item = DictParser.parse(station["attributes"])  # title->name, address->addr_full, lat/lng, phone
            item["ref"] = str(station["id"])
            item["branch"] = item.pop("name")

            services = [
                category["attributes"]["title"]
                for category in (station["attributes"].get("network_categories") or {}).get("data", [])
            ]
            apply_yes_no(Extras.ATM, item, "Bankomat" in services)
            apply_yes_no(Extras.CAR_WASH, item, "Avtoyuma" in services)
            apply_yes_no(Fuel.CNG, item, "CNG qaz (Metan)" in services)
            apply_yes_no(Fuel.LPG, item, "Maye qaz postu (LPG)" in services or "QDM (Propan-Butan)" in services)
            apply_yes_no(Fuel.ELECTRIC, item, "Elektromobillərin doldurma xidməti" in services)
            apply_category(Categories.FUEL_STATION, item)
            yield item
