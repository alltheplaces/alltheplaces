import math
from typing import Any, AsyncIterator, Iterable

import pygeohash
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature

GEOHASH_ALPHABET = "0123456789bcdefghjkmnpqrstuvwxyz"
# The widget also shows the points of partner networks (Magyar Posta, InPost, Foxpost and so on) in many more countries.
# These are Packeta's own pick-up point and Z-Box networks, from https://widget.packeta.com/v6/vendors-configuration.js
COUNTRIES = "cz,hu,pl,ro,sk"
VENDOR_CODES = "CZ-GUIUAH,HU-ZBIBBU,PL-SPVQOM,RO-WGCPIB,SK-YDLAXG,CZ-JGUZHA,HU-ZQYRDW,RO-JJYUAT,SK-UTZCOP"
Z_BOX = {"brand": "Z-Box", "brand_wikidata": "Q121537464"}


class PacketaSpider(Spider):
    name = "packeta"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"X-API-Key": "9f1d27c6-f56c-4755-a92c-cafce7111291"}}

    # The API returns the nearest 100 matching pick-up points within 100km of the centre of the requested geohash, with no
    # pagination and whatever the Limit parameter is set to.
    MAX_RESULTS = 100
    MAX_RADIUS_KM = 100
    # A saturated cell this small would hold over 100 pick-up points within about 100m, so it is not split further.
    MIN_PRECISION = 7
    # Precision 3 cells (about 156 by 156km at the equator) covering all of the countries above.
    SEED_PRECISION = 3
    LAT_RANGE = (43.5, 55.0)
    LON_RANGE = (12.0, 30.0)

    async def start(self) -> AsyncIterator[JsonRequest]:
        seeds = {
            pygeohash.encode(lat / 2, lon / 2, self.SEED_PRECISION)
            for lat in range(int(self.LAT_RANGE[0] * 2), int(self.LAT_RANGE[1] * 2) + 1)
            for lon in range(int(self.LON_RANGE[0] * 2), int(self.LON_RANGE[1] * 2) + 1)
        }
        for geohash in sorted(seeds):
            yield self.make_request(geohash)

    def make_request(self, geohash: str) -> JsonRequest:
        return JsonRequest(
            f"https://web.widget.packeta.com/v6/pps/api/web/v5/pickupPoints/geohash/{geohash}"
            f"?Limit={self.MAX_RESULTS}&App_ApiKey=all&App_Countries={COUNTRIES}&App_VendorCodes={VENDOR_CODES}",
            cb_kwargs={"geohash": geohash},
        )

    @staticmethod
    def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great circle distance, which is what the API reports as distanceFromOrigin."""
        lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
        a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        return 2 * 6371 * math.asin(math.sqrt(a))

    def furthest_corner_km(self, origin: tuple[float, float], geohash: str) -> float:
        lat, lon, lat_err, lon_err = pygeohash.decode_exactly(geohash)
        return max(
            self.distance_km(*origin, lat + dlat, lon + dlon)
            for dlat in (-lat_err, lat_err)
            for dlon in (-lon_err, lon_err)
        )

    def parse(self, response: Response, geohash: str) -> Iterable[Any]:
        locations = response.json()
        if len(locations) < self.MAX_RESULTS:
            covered_km = self.MAX_RADIUS_KM
        else:
            covered_km = max(location["distanceFromOrigin"] for location in locations) / 1000
        origin = pygeohash.decode_exactly(geohash)[:2]

        # Every location within covered_km of the cell centre was returned, so only the parts of the cell outside
        # that circle need querying again.
        if covered_km > self.furthest_corner_km(origin, geohash):
            complete = [geohash]
        elif len(geohash) < self.MIN_PRECISION:
            complete = []
            for child in (geohash + char for char in GEOHASH_ALPHABET):
                if covered_km > self.furthest_corner_km(origin, child):
                    complete.append(child)
                else:
                    yield self.make_request(child)
        else:
            self.logger.warning(f"Results may be truncated in {geohash}")
            self.crawler.stats.inc_value("atp/packeta/truncated_cell")
            complete = [geohash]

        if not complete:
            return
        precision = len(complete[0])
        for location in locations:
            # Locations outside the complete cells are collected by the query for their own cell.
            coordinates = location["coordinates"]
            if pygeohash.encode(coordinates["latitude"], coordinates["longitude"], precision) not in complete:
                continue
            yield self.parse_location(location)

    def parse_location(self, location: dict) -> Feature:
        flags = location["flags"]

        item = Feature()
        item["ref"] = location["externalId"]
        item["lat"] = location["coordinates"]["latitude"]
        item["lon"] = location["coordinates"]["longitude"]
        item["website"] = "https://www.packeta.com/pick-up-points/{}".format(location["branchCode"])

        if flags["isBox"]:
            item.update(Z_BOX)
            apply_category(Categories.PARCEL_LOCKER, item)
            item["addr_full"] = location["address"]["name"].removeprefix("Z-BOX ")
        else:
            item["name"] = location["name"]
            item["addr_full"] = location["address"]["name"]
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = "Packeta"

        apply_yes_no(Extras.PARCEL_PICKUP, item, True)
        apply_yes_no(Extras.PARCEL_MAIL_IN, item, flags["isPacketConsignment"])
        apply_yes_no(PaymentMethods.CARDS, item, flags["isCreditCardPayment"])
        apply_yes_no(PaymentMethods.CASH, item, flags["isCashPayment"])
        match location.get("wheelchairAccessibility"):
            case "yes":
                apply_yes_no(Extras.WHEELCHAIR, item, True)
            case "no":
                apply_yes_no(Extras.WHEELCHAIR, item, False)

        item["opening_hours"] = self.parse_opening_hours(location["openingHours"]["regular"])
        return item

    @staticmethod
    def parse_opening_hours(regular: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, ranges in regular.items():
            if not ranges:
                oh.set_closed(day)
            for time_range in ranges:
                close = "24:00" if time_range["close"] == "23:59" else time_range["close"]
                oh.add_range(day, time_range["open"], close)
        return oh
