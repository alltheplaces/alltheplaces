from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.items import Feature


def add_it_ranges(oh: OpeningHours, string: str) -> None:
    oh.add_ranges_from_string(
        string,
        days=DAYS_IT,
        named_day_ranges=NAMED_DAY_RANGES_IT,
        named_times=NAMED_TIMES_IT,
        closed=CLOSED_IT,
        delimiters=DELIMITERS_IT,
    )


class PosteItalianeITSpider(Spider):
    name = "poste_italiane_it"
    item_attributes = {"operator": "Poste Italiane", "operator_wikidata": "Q495026"}
    custom_settings = {"CONCURRENT_REQUESTS_PER_DOMAIN": 1, "DOWNLOAD_DELAY": 2, "RETRY_TIMES": 10}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://mapcollection.poste.it/v2/map/geoListByComune",
            data={
                "tipoPunto": ["UfficioPostale"],
                "limit": 50,
                "offset": 0,
            },
            cb_kwargs={"offset": 0},
            meta={"download_timeout": 30},
        )

    def parse(self, response: Response, offset: int, **kwargs: Any) -> Any:
        locations = response.json().get("data", {}).get("listaPunti", [])

        for location in locations:
            # The endpoint includes a few non-mappable rows without coordinates.
            if not location.get("lat") or not location.get("lon"):
                continue
            yield self.parse_location(location)

        if len(locations) == 50:
            yield JsonRequest(
                url="https://mapcollection.poste.it/v2/map/geoListByComune",
                data={
                    "tipoPunto": ["UfficioPostale"],
                    "limit": 50,
                    "offset": offset + 50,
                },
                cb_kwargs={"offset": offset + 50},
                meta={"download_timeout": 30},
            )

    def parse_location(self, location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)

        item["ref"] = location.get("frazionario")
        item["lat"] = location.get("lat")
        item["lon"] = location.get("lon")
        item["street_address"] = location.get("indirizzoPunto")
        item["city"] = location.get("citta")
        item["postcode"] = location.get("cap")
        item["phone"] = location.get("numeroTelefono")
        item["branch"] = location.get("nomePunto")
        item["name"] = f'Ufficio Postale {item["branch"]}' if item.get("branch") else None
        item["extras"]["post_office"] = "bureau"

        if fax := location.get("fax"):
            item["extras"]["contact:fax"] = fax

        apply_category(Categories.POST_OFFICE, item)
        apply_yes_no(Extras.WIFI, item, any(service.get("codice") == "WIFI" for service in location.get("servizi", [])))
        apply_yes_no(
            Extras.ATM,
            item,
            any(service.get("codice") in ("ATMNONH24", "ATMH24") for service in location.get("servizi", [])),
        )
        self.apply_hours(item, location.get("orari"))

        return item

    def apply_hours(self, item: Feature, hours: list[dict[str, Any]] | None) -> None:
        if not hours:
            return

        oh = OpeningHours()
        try:
            for day_h in hours:
                add_it_ranges(oh, f'{day_h["giorno"]}: {day_h["orario"]}')
        except Exception:
            self.logger.warning("Unable to parse opening hours: {}".format(hours))
            return
        item["opening_hours"] = oh
