import json
import urllib.parse
from typing import AsyncIterator

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import make_subdivisions
from locations.items import Feature, set_closed


class ChargepointSpider(Spider):
    name = "chargepoint"
    item_attributes = {"brand": "ChargePoint", "brand_wikidata": "Q5176149"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

    def make_request(self, bounds=(-180.0, -90.0, 180.0, 90.0), page_offset="", page=0):
        query = {
            "station_list": {
                "sw_lon": bounds[0],
                "sw_lat": bounds[1],
                "ne_lon": bounds[2],
                "ne_lat": bounds[3],
                "page_size": 50,
                "page_offset": page_offset,
            }
        }
        return JsonRequest(
            url="https://mc.chargepoint.com/map-prod/v2?"
            + urllib.parse.quote(json.dumps(query, separators=(",", ":")).encode("utf-8")),
            method="POST",
            cb_kwargs={"bounds": bounds, "page": page},
        )

    async def start(self):
        for bounds in make_subdivisions((-180.0, -90.0, 180.0, 90.0), 2):
            yield self.make_request(bounds)

    def parse(self, response, bounds, page):
        if "error" in response.json():
            self.logger.error("Server error: " + response.json()["error"])
            if "station_list" not in response.json():
                return get_retry_request(
                    response.request,
                    spider=self,
                    reason=response.json()["error"],
                )

        station_list = response.json()["station_list"]

        if "error" in station_list:
            self.logger.error("Request error: " + station_list["error"])

        if station_list.get("page_offset") != "last_page":
            # More pages
            yield self.make_request(bounds, station_list["page_offset"], page=page + 1)
        elif page == 1 and len(station_list.get("stations", [])) >= 50 and (st["ne_lon"] - st["sw_lon"]) > 8.6e-05:
            # Even paginated results have a result limit. Try with a narrower area, if possible.
            for sub_bounds in make_subdivisions(bounds, 2):
                yield self.make_request(sub_bounds)

        for station in station_list.get("stations", []):
            item = Feature(
                lat=station["lat"],
                lon=station["lon"],
                ref=station["device_id"],
                name=f"{station.get('name1', '')} {station.get('name2', '')}".strip(),
                street_address=station.get("address1"),
                city=station.get("city"),
                website=f"https://driver.chargepoint.com/stations/{station['device_id']}",
            )

            apply_yes_no(
                Extras.WHEELCHAIR, item, station.get("parking_accessibility") in ("DISABLED_PARKING", "VAN_ACCESSIBLE")
            )
            apply_yes_no(Extras.FEE, item, station["payment_type"] != "free", False)
            if station["tou_status"] == "close":
                # indicates temporary closure - is set_closed right to use?
                set_closed(item)
            apply_yes_no(f"currency:{station.get('currency_iso_code')}", item, "currency_iso_code" in station)
            if station.get("access_restriction", "NONE") != "NONE":
                item["extras"]["access"] = "private"
            if "max_power" in station:
                item["extras"][
                    "socket:unknown:output"
                ] = f"{station['max_power']['max']} {station['max_power']['unit']}"
            if "ports" in station:
                item["extras"]["capacity"] = len(station["ports"])
            item["extras"]["network"] = station["network_display_name"]

            apply_category(Categories.CHARGE_POINT, item)

            yield item
