import json
import random
import urllib.parse

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class ChargePointSpider(scrapy.Spider):
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
            meta={"bounds": bounds},
        )

    def parse(self, response):
        self.logger.info(response.json())
