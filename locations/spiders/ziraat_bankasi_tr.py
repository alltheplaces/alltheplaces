from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

SOURCE_URL = "https://www.ziraatbank.com.tr/tr/bize-ulasin/sube-ve-atmler"
API_URL = "https://www.ziraatbank.com.tr/tr/_layouts/15/Ziraat/SubeATM/Ajax.aspx"
HEADERS = {"Referer": SOURCE_URL, "X-Requested-With": "XMLHttpRequest"}

LOCATION_TYPES = {
    "branch": {"category": Categories.BANK, "list_method": "GetAllSubeText", "width": 8},
    "atm": {"category": Categories.ATM, "list_method": "GetAllAtmText", "width": 7},
}


class ZiraatBankasiTRSpider(Spider):
    name = "ziraat_bankasi_tr"
    item_attributes = {"brand": "Ziraat Bankası", "brand_wikidata": "Q696003"}

    async def start(self) -> AsyncIterator[Any]:
        yield Request(SOURCE_URL, callback=self.parse_finder)

    def parse_finder(self, response: Response) -> Any:
        states = {
            option.attrib["value"]: option.xpath("normalize-space()").get()
            for option in response.css("#ddlCity option")
            if option.attrib.get("value") and option.attrib["value"] != "0"
        }

        for location_type, settings in LOCATION_TYPES.items():
            yield JsonRequest(
                url=f"{API_URL}/{settings['list_method']}",
                data={},
                headers=HEADERS,
                callback=self.parse_location_list,
                cb_kwargs={"location_type": location_type, "states": states},
            )

    def parse_location_list(self, response: Response, location_type: str, states: dict[str, str]) -> Any:
        settings = LOCATION_TYPES[location_type]
        data = response.json()["d"]["Data"]
        parts = data.split("|")

        if len(parts) % settings["width"] != 0:
            self.logger.error("Unexpected %s payload width from %s", location_type, response.url)
            return

        for index in range(0, len(parts), settings["width"]):
            fields = parts[index : index + settings["width"]]
            state = states.get(fields[-2])
            if not state:
                self.crawler.stats.inc_value(f"atp/{self.name}/skipped_unknown_state")
                continue

            item = Feature(
                ref=f"{location_type}-{fields[0]}",
                lat=fields[1].replace(",", "."),
                lon=fields[2].replace(",", "."),
                state=state,
            )
            apply_category(settings["category"], item)
            yield item
