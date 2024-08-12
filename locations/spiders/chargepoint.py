import json
import urllib.parse

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class ChargepointSpider(scrapy.Spider):
    name = "chargepoint"
    item_attributes = {"brand": "ChargePoint", "brand_wikidata": "Q5176149"}

    def start_requests(self):
        bounds = (-180.0, -90.0, 180.0, 90.0)
        query = {
            "map_data": {
                "screen_width": 1024,
                "screen_height": 1024,
                "sw_lon": bounds[0],
                "sw_lat": bounds[1],
                "ne_lon": bounds[2],
                "ne_lat": bounds[3],
                "filter": {
                    "connector_l1": False,
                    "connector_l2": False,
                    "is_bmw_dc_program": False,
                    "is_nctc_program": False,
                    "connector_chademo": False,
                    "connector_combo": False,
                    "connector_tesla": False,
                    "price_free": False,
                    "status_available": False,
                    "network_chargepoint": True,
                    "network_blink": False,
                    "network_semacharge": False,
                    "network_evgo": False,
                    "connector_l2_nema_1450": False,
                    "connector_l2_tesla": False,
                },
            }
        }
        yield scrapy.http.JsonRequest(
            url="https://mc.chargepoint.com/map-prod/get?" + urllib.parse.quote(json.dumps(query).encode("utf8")),
            method="GET",
        )

    def parse(self, response):
        response_data = response.json()["map_data"]

        for summary in response_data.get("summaries"):
            port_count = summary.get("port_count", {}).get("total", 0)

            if port_count < 100:
                # If there's a small-ish number of ports in this summary bounding box
                # then request station list for the bbox

                # If there's a single station here, the bounding box will have zero area
                # around the point, and the API doesn't like that. So we make it a little
                # bigger manually.
                if summary["ne_lon"] - summary["sw_lon"] < 0.001:
                    summary["ne_lon"] += 0.01
                    summary["sw_lon"] -= 0.01
                if summary["ne_lat"] - summary["sw_lat"] < 0.001:
                    summary["ne_lat"] += 0.01
                    summary["sw_lat"] -= 0.01

                query = {
                    "station_list": {
                        "screen_width": 1024,
                        "screen_height": 1024,
                        "sw_lon": summary["sw_lon"],
                        "sw_lat": summary["sw_lat"],
                        "ne_lon": summary["ne_lon"],
                        "ne_lat": summary["ne_lat"],
                        "page_size": 100,
                        "page_offset": "",
                        "filter": {
                            "connector_l1": False,
                            "connector_l2": False,
                            "is_bmw_dc_program": False,
                            "is_nctc_program": False,
                            "connector_chademo": False,
                            "connector_combo": False,
                            "connector_tesla": False,
                            "price_free": False,
                            "status_available": False,
                            "network_chargepoint": True,
                            "network_blink": False,
                            "network_semacharge": False,
                            "network_evgo": False,
                            "connector_l2_nema_1450": False,
                            "connector_l2_tesla": False,
                        },
                    }
                }
                yield scrapy.http.JsonRequest(
                    url="https://mc.chargepoint.com/map-prod/get?"
                    + urllib.parse.quote(json.dumps(query).encode("utf8")),
                    method="GET",
                    callback=self.parse_station_list,
                )

            else:
                # Otherwise make another map data request for the summary bounding box, simulating zooming in
                query = {
                    "map_data": {
                        "screen_width": 1024,
                        "screen_height": 1024,
                        "sw_lon": summary["sw_lon"],
                        "sw_lat": summary["sw_lat"],
                        "ne_lon": summary["ne_lon"],
                        "ne_lat": summary["ne_lat"],
                        "filter": {
                            "connector_l1": False,
                            "connector_l2": False,
                            "is_bmw_dc_program": False,
                            "is_nctc_program": False,
                            "connector_chademo": False,
                            "connector_combo": False,
                            "connector_tesla": False,
                            "price_free": False,
                            "status_available": False,
                            "network_chargepoint": True,
                            "network_blink": False,
                            "network_semacharge": False,
                            "network_evgo": False,
                            "connector_l2_nema_1450": False,
                            "connector_l2_tesla": False,
                        },
                    }
                }
                yield scrapy.http.JsonRequest(
                    url="https://mc.chargepoint.com/map-prod/get?"
                    + urllib.parse.quote(json.dumps(query).encode("utf8")),
                    method="GET",
                )

    def parse_station_list(self, response):
        station_list = response.json()["station_list"]

        for summary in station_list.get("summaries"):
            properties = {
                "ref": summary["device_id"],
                "lat": summary["lat"],
                "lon": summary["lon"],
                "name": " ".join(summary.get("station_name", [])) or None,
                "city": summary.get("address", {}).get("city"),
                "state": summary.get("address", {}).get("state_name"),
                "street_address": summary.get("address", {}).get("address1"),
            }

            apply_category(Categories.CHARGING_STATION, properties)

            properties["extras"]["capacity"] = summary["port_count"]["total"]

            yield Feature(**properties)
