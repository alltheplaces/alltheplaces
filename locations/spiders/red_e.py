from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

FEED = "https://redecharge-webhook.netlify.app/.netlify/functions/locations-json"

SOCKET_TYPES = {
    "CCS1": "type1_combo",
    "CCS2": "type2_combo",
    "CHAdeMO": "chademo",
    "J1772": "type1",
    "MENNEKES": "type2",
    "NACS": "nacs",
    "TESLA_S": "nacs",
}

GONE = {"REMOVED"}

COUNTRIES = {"USA": "US", "CAN": "CA"}

STATES = {
    "Alberta": "AB", "British Columbia": "BC", "Manitoba": "MB", "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL", "Northwest Territories": "NT", "Nova Scotia": "NS",
    "Nunavut": "NU", "Ontario": "ON", "Prince Edward Island": "PE", "Quebec": "QC",
    "Saskatchewan": "SK", "Yukon": "YT",
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}


def parse_sockets(connectors: list[dict]) -> dict[str, str]:
    """Socket counts and per-type peak output, ignoring removed hardware."""
    counts: dict[str, int] = {}
    outputs: dict[str, float] = {}
    for connector in connectors or []:
        if connector.get("status") in GONE:
            continue
        socket = SOCKET_TYPES.get(connector.get("standard"))
        if socket is None:
            continue
        counts[socket] = counts.get(socket, 0) + 1
        if kw := connector.get("kw"):
            outputs[socket] = max(outputs.get(socket, 0), float(kw))
    if not counts:
        return {}
    extras = {f"socket:{socket}": str(count) for socket, count in counts.items()}
    extras.update({f"socket:{socket}:output": f"{output:g} kW" for socket, output in outputs.items()})
    extras["capacity"] = str(sum(counts.values()))
    return extras


class RedESpider(Spider):
    name = "red_e"
    item_attributes = {
        "brand": "Red E",
        "operator": "Red E",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(FEED, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        locations = response.json()
        if not locations:
            self.logger.error("{} returned no locations".format(FEED))
            self.crawler.stats.inc_value(f"atp/{self.name}/empty_feed")
            return

        for location in locations:
            item = Feature(
                {
                    "ref": str(location["id"]),
                    "name": location.get("name"),
                    "street_address": (location.get("address") or "").split(",")[0].strip() or None,
                    "city": location.get("city"),
                    "state": STATES.get(location.get("state"), location.get("state")),
                    "country": COUNTRIES.get(location.get("country"), location.get("country")),
                    "lat": location.get("lat"),
                    "lon": location.get("lng"),
                }
            )
            item["extras"] = {"access": "yes"}
            item["extras"].update(parse_sockets(location.get("connectors")))

            apply_category(Categories.CHARGING_STATION, item)
            yield item
