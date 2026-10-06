import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import bbox_contains, make_subdivisions
from locations.hours import DAYS_FI, OpeningHours, sanitise_day
from locations.items import Feature

POSTI = {"operator": "Posti", "operator_wikidata": "Q843453"}
POSTI_BRAND = {"brand": "Posti", "brand_wikidata": "Q843453"}

LETTERBOX_QUERY = """
query Letterboxes($southWestLatitude: Float!, $southWestLongitude: Float!, $northEastLatitude: Float!, $northEastLongitude: Float!) {
  findLetterboxLocations(
    acceptLanguage: ["fi"]
    queryParams: {
      limit: 50
      rectangle: {
        southWestLatitude: $southWestLatitude
        southWestLongitude: $southWestLongitude
        northEastLatitude: $northEastLatitude
        northEastLongitude: $northEastLongitude
      }
    }
  ) {
    letterBoxes {
      id
      name
      streetAddress
      postcode
      postcodeName
      emptyingDays
      humanReadableEmptyingTimes { lastEmptying languageCode }
      coordinates { latitude longitude }
    }
  }
}
"""

SERVICE_POINT_QUERY = """
query ServicePoints($southWestLatitude: Float!, $southWestLongitude: Float!, $northEastLatitude: Float!, $northEastLongitude: Float!, $sapProfileCodes: [String!]) {
  findServicePointLocations(
    acceptLanguage: ["fi"]
    includeHiddenServicePoints: false
    queryParams: {
      limit: 50
      filter: { siteAccess: PUBLIC, sapProfileCode: $sapProfileCodes }
      rectangle: {
        southWestLatitude: $southWestLatitude
        southWestLongitude: $southWestLongitude
        northEastLatitude: $northEastLatitude
        northEastLongitude: $northEastLongitude
      }
    }
  ) {
    servicePoints {
      pupCode
      status
      sapProfile { code }
      addresses { publicName streetAddress postcode city specificLocation countryCode languageCode }
      capabilities { name value }
      availability {
        openingHours { opens closes closed dayOfWeek open24h }
      }
      coordinates { latitude longitude }
    }
  }
}
"""

# Service point profile codes, from the posti.fi map's own JavaScript.
# Posti's own full service points ("Posti" stores and the Santa Claus Main Post Office).
POSTI_OFFICE_CODES = {"0"}
# Posti business service points ("Yrityspiste"), at Posti's own terminals.
POSTI_BUSINESS_CODES = {"4"}
# Counters in shops, kiosks and supermarkets run by partners: sales points
# (myyntipiste), parcel pickup points (noutopiste, lähipiste) and letter points.
PARTNER_CODES = {
    "1",
    "2",
    "3",
    "8",
    "10",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
}
# Parcel lockers (90, 91) and Helposti drop-off points (35) are not requested.
COUNTER_CODES = sorted(POSTI_OFFICE_CODES | POSTI_BUSINESS_CODES | PARTNER_CODES, key=int)

EMPTYING_TIME = re.compile(r"\b([a-zäö]{2})(?:\s*-\s*([a-zäö]{2}))?\s+(\d{1,2})[.:](\d{2})\b", re.IGNORECASE)


class PostiFISpider(Spider):
    name = "posti_fi"
    custom_settings = {"CONCURRENT_REQUESTS": 4, "DOWNLOAD_DELAY": 0.25}

    # Both queries error above 50 results and have no pagination; results are the
    # 50 nearest the centre of the rectangle, so saturated rectangles are split.
    MAX_RESULTS = 50
    # Hidden service points are removed after the limit is applied, so a
    # saturated service point query can return a few less than 50.
    SERVICE_POINT_SPLIT_AT = 40
    MIN_CELL_DEGREES = 0.002
    # lon_min, lat_min, lon_max, lat_max. Offset so that no edge falls on a
    # whole degree: the API returns nothing if any coordinate is an integer.
    FI_BOUNDS = (19.0013, 59.6013, 31.6013, 70.1013)

    token: str

    async def start(self) -> AsyncIterator[JsonRequest]:
        await self.refresh_token()
        yield self.make_request("letterbox", self.FI_BOUNDS)
        yield self.make_request("service_point", self.FI_BOUNDS)

    async def refresh_token(self) -> None:
        response = await self.crawler.engine.download_async(
            JsonRequest("https://auth-service.posti.fi/api/v1/anonymous_token", data={}, dont_filter=True)
        )
        self.token = response.json()["role_tokens"][0]["token"]

    @staticmethod
    def non_integer(value: float) -> float:
        return value + 0.0001 if abs(value - round(value)) < 0.00001 else value

    def make_request(self, kind: str, bounds: tuple[float, float, float, float]) -> JsonRequest:
        lon_min, lat_min, lon_max, lat_max = (self.non_integer(v) for v in bounds)
        variables = {
            "southWestLatitude": lat_min,
            "southWestLongitude": lon_min,
            "northEastLatitude": lat_max,
            "northEastLongitude": lon_max,
        }
        if kind == "letterbox":
            query = LETTERBOX_QUERY
        else:
            query = SERVICE_POINT_QUERY
            variables["sapProfileCodes"] = COUNTER_CODES
        return JsonRequest(
            "https://graphql.posti.fi/graphql",
            data={"query": query, "variables": variables},
            headers={"authorization": self.token},
            meta={"handle_httpstatus_list": [401]},
            cb_kwargs={"kind": kind, "bounds": bounds},
            dont_filter=True,
        )

    async def parse(
        self, response: Response, kind: str, bounds: tuple[float, float, float, float]
    ) -> AsyncIterator[Any]:
        if response.status == 401:
            # The anonymous token expires after an hour; queued requests still carry the old one.
            if response.request.headers.get("authorization") == self.token.encode():
                await self.refresh_token()
            yield self.make_request(kind, bounds)
            return

        data = response.json()
        if data.get("errors"):
            self.logger.error(f"GraphQL errors for {kind} {bounds}: {data['errors']}")
            self.crawler.stats.inc_value(f"atp/posti_fi/graphql_error/{kind}")
            return

        if kind == "letterbox":
            locations = (data["data"]["findLetterboxLocations"] or {}).get("letterBoxes") or []
            saturated = len(locations) >= self.MAX_RESULTS
        else:
            locations = (data["data"]["findServicePointLocations"] or {}).get("servicePoints") or []
            saturated = len(locations) >= self.SERVICE_POINT_SPLIT_AT

        if saturated:
            lon_min, lat_min, lon_max, lat_max = bounds
            if max(lon_max - lon_min, lat_max - lat_min) > self.MIN_CELL_DEGREES:
                for child in make_subdivisions(bounds, 2):
                    yield self.make_request(kind, child)
                return
            self.logger.warning(f"Results may be truncated for {kind} in {bounds}")
            self.crawler.stats.inc_value(f"atp/posti_fi/truncated_cell/{kind}")

        for location in locations:
            # Locations outside this cell are collected by the query for their own cell.
            if not bbox_contains(bounds, (location["coordinates"]["longitude"], location["coordinates"]["latitude"])):
                continue
            if kind == "letterbox":
                yield self.parse_letterbox(location)
            else:
                for item in self.parse_service_point(location):
                    yield item

    def parse_letterbox(self, location: dict) -> Feature:
        item = Feature()
        item["ref"] = str(location["id"])
        item["lat"] = location["coordinates"]["latitude"]
        item["lon"] = location["coordinates"]["longitude"]
        item["street_address"] = location.get("streetAddress")
        item["postcode"] = location.get("postcode")
        if city := location.get("postcodeName"):
            item["city"] = city.title()
        item["country"] = "FI"
        apply_category(Categories.POST_BOX, item)
        item.update(POSTI)
        # The box's location as shown on the map, e.g. "KULOSAAREN METROASEMA".
        if location.get("name"):
            item["extras"]["description"] = location["name"]
        if collection_times := self.parse_collection_times(location.get("humanReadableEmptyingTimes") or []):
            item["extras"]["collection_times"] = collection_times
        return item

    @staticmethod
    def parse_collection_times(emptying_times: list[dict]) -> str | None:
        # e.g. "ma-pe 12.00" (Monday to Friday, last collection at 12:00).
        rules = []
        for emptying_time in emptying_times:
            for start_day, end_day, hour, minute in EMPTYING_TIME.findall(emptying_time.get("lastEmptying") or ""):
                start = sanitise_day(start_day, DAYS_FI)
                end = sanitise_day(end_day, DAYS_FI) if end_day else None
                if not start or (end_day and not end):
                    return None
                days = f"{start}-{end}" if end else start
                rules.append(f"{days} {int(hour):02d}:{minute}")
        return "; ".join(dict.fromkeys(rules)) or None

    def parse_service_point(self, location: dict) -> Iterable[Feature]:
        code = (location.get("sapProfile") or {}).get("code")
        addresses = location.get("addresses") or []
        address = next((a for a in addresses if a.get("languageCode") == "fi"), addresses[0] if addresses else {})
        if address.get("countryCode") not in (None, "FI"):
            # The same service also covers the Baltic states.
            return

        item = Feature()
        item["ref"] = location["pupCode"]
        item["lat"] = location["coordinates"]["latitude"]
        item["lon"] = location["coordinates"]["longitude"]
        item["street_address"] = address.get("streetAddress")
        item["postcode"] = address.get("postcode")
        if city := address.get("city"):
            item["city"] = city.title() if city.isupper() else city
        item["country"] = "FI"
        if address.get("specificLocation"):
            item["extras"]["description"] = address["specificLocation"]
        item["opening_hours"] = self.parse_opening_hours((location.get("availability") or {}).get("openingHours"))

        capabilities = {}
        for capability in location.get("capabilities") or []:
            capabilities.setdefault(capability["name"], set()).add(capability["value"])
        apply_yes_no(
            "post_office:letter_from", item, "LETTER_DROP_OFF" in capabilities.get("letterDropOff", set()), False
        )
        parcel_dropoff = capabilities.get("parcelDropoff", set())
        apply_yes_no(Extras.PARCEL_MAIL_IN, item, bool(parcel_dropoff - {"NO_DROPOFF"}), False)
        apply_yes_no(Extras.PARCEL_PICKUP, item, "AVAILABLE" in capabilities.get("parcelPickup", set()), False)

        public_name = (address.get("publicName") or "").strip()
        branch = public_name.removeprefix("Posti, ").removeprefix("Postipiste, ").strip()
        if code in POSTI_OFFICE_CODES:
            apply_category(Categories.POST_OFFICE, item)
            item.update(POSTI | POSTI_BRAND)
            item["name"] = "Posti"
            item["branch"] = branch.removeprefix("Posti, ").removeprefix("POSTI ").strip()
        elif code in POSTI_BUSINESS_CODES:
            apply_category(Categories.POST_OFFICE, item)
            item.update(POSTI | POSTI_BRAND)
            item["name"] = "Posti Yrityspiste"
            item["branch"] = branch.removeprefix("Yrityspiste, ").removeprefix("Yrityspiste ").strip()
        elif code in PARTNER_CODES:
            apply_category(Categories.GENERIC_POI, item)
            item["name"] = branch
            # Run by the host shop, not by Posti, so no operator is set.
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = POSTI_BRAND["brand"]
            item["extras"]["post_office:brand:wikidata"] = POSTI_BRAND["brand_wikidata"]
        else:
            self.crawler.stats.inc_value(f"atp/posti_fi/unknown_profile/{code}")
            return
        yield item

    @staticmethod
    def parse_opening_hours(rules: list[dict] | None) -> OpeningHours | None:
        if not rules:
            return None
        oh = OpeningHours()
        for rule in rules:
            if rule.get("closed"):
                oh.set_closed(rule["dayOfWeek"])
            elif rule.get("open24h"):
                oh.add_range(rule["dayOfWeek"], "00:00", "24:00")
            elif rule.get("opens") and rule.get("closes"):
                oh.add_range(rule["dayOfWeek"], rule["opens"], rule["closes"], "%H:%M:%S")
        return oh
