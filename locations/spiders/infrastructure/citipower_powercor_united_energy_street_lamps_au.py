from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import bbox_split
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class CitipowerPowercorUnitedEnergyStreetLampsAUSpider(Spider):
    name = "citipower_powercor_united_energy_street_lamps_au"
    item_attributes = {"state": "VIC", "nsi_id": "N/A"}
    allowed_domains = ["publiclighting.portal.powercor.com.au"]
    start_urls = ["https://publiclighting.portal.powercor.com.au/PublicLightFault"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    _request_attribs: dict = {}  # Authorization token and other attributes
    # captured once and required to be sent with
    # each API request.
    _tid_counter: int = 0  # Transaction ID counter the API uses.

    @staticmethod
    def get_victoria_bboxes() -> list[tuple[tuple[float, float], tuple[float, float]]]:
        lat_n = -33.97  # Murray River SA/VIC border
        lon_e = 146.29  # Wangaratta (nothing East of this city)
        lat_s = -38.86  # Cape Otway (nothing South of this point)
        lon_w = 140.96  # Murray River SA/VIC border
        return bbox_split(((lat_n, lon_w), (lat_s, lon_e)), lat_parts=8, lon_parts=8, precision=4)

    def make_bbox_search_request(
        self, bbox: tuple[tuple[float, float], tuple[float, float]], level: int = 1
    ) -> JsonRequest:
        lon_se = bbox[1][1]
        lat_se = bbox[1][0]
        lon_nw = bbox[0][1]
        lat_nw = bbox[0][0]
        bbox_string = f"{lon_se},{lat_se},{lon_nw},{lat_nw}"
        data = {
            "action": "PublicLightFaultController",
            "ctx": {
                "authorization": self._request_attribs["authorization"],
                "csrf": self._request_attribs["csrf"],
                "ns": self._request_attribs["ns"],
                "ver": round(float(self._request_attribs["ver"])),
                "vid": self._request_attribs["vid"],
            },
            "data": [bbox_string],
            "method": "findLamps",
            "tid": self._tid_counter,
            "type": "rpc",
        }
        headers = {
            "Origin": "https://publiclighting.portal.powercor.com.au",
            "Referer": "https://publiclighting.portal.powercor.com.au/PublicLightFault",
            "X-Requested-With": "XMLHttpRequest",
            "X-User-Agent": "Visualforce-Remoting",
        }
        self._tid_counter = self._tid_counter + 1
        return JsonRequest(
            url="https://publiclighting.portal.powercor.com.au/apexremote",
            data=data,
            headers=headers,
            meta={"bbox": bbox, "level": level},
            method="POST",
            callback=self.parse_street_lamps,
        )

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        js_object = response.xpath('//script[contains(text(), "findLamps")]/text()').get()
        request_attribs_js = "{" + js_object.split('{"name":"findLamps",', 1)[1].split("}", 1)[0] + "}"
        self._request_attribs = parse_js_object(request_attribs_js)
        self._request_attribs["vid"] = js_object.split('"vid":"', 1)[1].split('"', 1)[0]
        for bbox in self.get_victoria_bboxes():
            yield self.make_bbox_search_request(bbox)

    def parse_street_lamps(self, response: Response) -> Iterable[Feature | JsonRequest]:
        bbox_string = "NW:[{},{}] SE:[{},{}]".format(
            response.meta["bbox"][0][0],
            response.meta["bbox"][0][1],
            response.meta["bbox"][1][0],
            response.meta["bbox"][1][1],
        )
        if response.json()[0]["statusCode"] != 200:
            raise RuntimeError(
                "Server returned an error code to a request for street lamps in the bounding box of {}.".format(
                    bbox_string
                )
            )
        if "result" not in response.json()[0].keys():
            # No street lamps exist in the requested bounding box.
            self.crawler.stats.inc_value("atp/geo_search/misses")
            return
        level = response.meta["level"]
        if level == 4:
            self.crawler.stats.max_value(
                "atp/geo_search/max_features_returned/level4", len(response.json()[0]["result"]["items"])
            )
        if len(response.json()[0]["result"]["items"]) == 1000:
            self.crawler.stats.inc_value("atp/geo_search/misses")
            self.crawler.stats.inc_value(f"atp/geo_search/misses/level{level}")
            if level == 1:
                lat_lon_parts = 6
            elif level == 2:
                lat_lon_parts = 4
            elif level == 3:
                lat_lon_parts = 4
            else:
                raise RuntimeError(
                    "More than 4 levels of subdivision of bounding boxes were unexpectedly encountered. Crawling stopped to avoid an endless recursive loop."
                )
            for bbox in bbox_split(
                response.meta["bbox"], lat_parts=lat_lon_parts, lon_parts=lat_lon_parts, precision=4
            ):
                yield self.make_bbox_search_request(bbox, level=level + 1)
            return
        self.crawler.stats.inc_value("atp/geo_search/hits")
        self.crawler.stats.inc_value(f"atp/geo_search/hits/level{level}")
        if isinstance(response.json()[0]["result"]["items"], dict):
            street_lamps = [response.json()[0]["result"]["items"]]
        else:
            street_lamps = response.json()[0]["result"]["items"]
        for street_lamp in street_lamps:
            if street_lamp.get("company") not in ["CP", "PCOR", "UE"]:
                continue
            properties = {
                "ref": street_lamp["id"],
                "lat": street_lamp["y"],
                "lon": street_lamp["x"],
            }
            apply_category(Categories.STREET_LAMP, properties)
            if pole_id := street_lamp.get("pole_no"):
                properties["extras"]["alt_ref"] = pole_id
            match street_lamp["company"]:
                case "CP":
                    properties["operator"] = "CitiPower"
                    properties["operator_wikidata"] = "Q133890760"
                case "PCOR":
                    properties["operator"] = "Powercor"
                    properties["operator_wikidata"] = "Q7236677"
                case "UE":
                    properties["operator"] = "United Energy"
                    properties["operator_wikidata"] = "Q48790747"
                case _:
                    self.logger.warning("Unknown street lamp operator: {}".format(street_lamp["company"]))
            yield Feature(**properties)
