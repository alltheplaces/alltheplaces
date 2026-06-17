from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Polish day abbreviation keys in the opening_hours API field → ISO day abbreviations
PL_DAYS = {
    "PON": "Mo",
    "WT": "Tu",
    "SR": "We",
    "CZW": "Th",
    "PT": "Fr",
    "SOB": "Sa",
    "NIEDZ": "Su",
}

DHL_BOX_BRAND = "DHL BOX 24/7"
DHL_BOX_WIKIDATA = "Q115568785"
DHL_POP_BRAND = "DHL"
DHL_POP_WIKIDATA = "Q489815"


class DhlPLSpider(Spider):
    """DHL parcel pick-up points and parcel lockers (DHL BOX 24/7) in Poland.

    Data comes from two endpoints on parcelshop.dhl.pl:
      - /mapa/points  returns all ~24 000 location IDs, lat/lon, and type
      - /mapa/point?id=<ID>  returns full address, name, and opening hours
    """

    name = "dhl_pl"
    item_attributes = {"brand": DHL_POP_BRAND, "brand_wikidata": DHL_POP_WIKIDATA}
    allowed_domains = ["parcelshop.dhl.pl"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    POINTS_URL = "https://parcelshop.dhl.pl/mapa/points"
    DETAIL_URL = "https://parcelshop.dhl.pl/mapa/point?id={id}"

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            self.POINTS_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AllThePlaces/1.0)"},
            callback=self.parse_points,
        )

    def parse_points(self, response: Response, **kwargs: Any) -> Any:
        for point in response.json():
            yield Request(
                self.DETAIL_URL.format(id=point["ID"]),
                headers={"User-Agent": "Mozilla/5.0 (compatible; AllThePlaces/1.0)"},
                callback=self.parse_detail,
                cb_kwargs={
                    "point_type": point.get("P_TYPE", ""),
                    "lat": point.get("SZ_GEOGRAFICZNA"),
                    "lon": point.get("DL_GEOGRAFICZNA"),
                },
            )

    def parse_detail(self, response: Response, point_type: str, lat: str, lon: str, **kwargs: Any) -> Any:
        payload = response.json()
        if payload.get("status") != "ok":
            return
        data = payload["data"]

        item = Feature()
        item["ref"] = str(data["id"])
        item["name"] = data.get("name")
        street = data.get("street", "")
        street_no = data.get("streetNo") or data.get("houseNo") or ""
        item["street_address"] = f"{street} {street_no}".strip() or None
        item["postcode"] = data.get("zip")
        item["city"] = data.get("city")
        item["country"] = "PL"
        item["lat"] = lat
        item["lon"] = lon

        # Parse structured opening hours
        oh_data = data.get("opening_hours") or {}
        if oh_data:
            oh = OpeningHours()
            for pl_day, iso_day in PL_DAYS.items():
                open_time = oh_data.get(f"{pl_day}_open")
                close_time = oh_data.get(f"{pl_day}_close")
                if open_time and close_time:
                    oh.add_range(iso_day, open_time, close_time)
            item["opening_hours"] = oh

        # Assign brand and category by location type
        if point_type == "ecobox":
            # Automated parcel locker (DHL BOX 24/7)
            item["brand"] = DHL_BOX_BRAND
            item["brand_wikidata"] = DHL_BOX_WIKIDATA
            apply_category(Categories.PARCEL_LOCKER, item)
        else:
            # Partner pick-up / drop-off point (Żabka, InMedio, Lewiatan, etc.)
            item["brand"] = DHL_POP_BRAND
            item["brand_wikidata"] = DHL_POP_WIKIDATA
            apply_category(Categories.POST_OFFICE, item)
            item["extras"]["post_office"] = "post_partner"

        yield item
