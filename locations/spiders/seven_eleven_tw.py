import re
from typing import Any

import xmltodict
from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenTWSpider(Spider):
    name = "seven_eleven_tw"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://emap.pcsc.com.tw/lib/areacode.js"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for city, city_id in re.findall(r"new AreaNode\(\'(.+?)\',.+?\'(\d+)\'\),", response.text):
            yield FormRequest(
                url="https://emap.pcsc.com.tw/EMapSDK.aspx",
                formdata={"commandid": "GetTown", "cityid": city_id},
                callback=self.parse_towns,
                cb_kwargs=dict(city=city),
            )

    def parse_towns(self, response: Response, city: str) -> Any:
        for town in xmltodict.parse(response.text)["iMapSDKOutput"].get("GeoPosition", []):
            yield FormRequest(
                url="https://emap.pcsc.com.tw/EMapSDK.aspx",
                formdata={"commandid": "SearchStore", "city": city, "town": town["TownName"]},
                callback=self.parse_locations,
                cb_kwargs=dict(city=city),
            )

    def parse_locations(self, response: Response, city: str) -> Any:
        locations = xmltodict.parse(response.text)["iMapSDKOutput"].get("GeoPosition", [])
        if isinstance(locations, dict):
            locations = [locations]
        for location in locations:
            item = Feature()
            item["ref"] = location.get("POIID")
            item["branch"] = location.get("POIName")
            item["city"] = city
            item["addr_full"] = location.get("Address")
            item["phone"] = location.get("Telno")
            item["extras"]["fax"] = location.get("FaxNo")
            item["lat"] = re.sub(r"(\d{2})(\d+)", r"\1.\2", location.get("Y", "").replace(".", ""))
            item["lon"] = re.sub(r"(\d{3})(\d+)", r"\1.\2", location.get("X", "").replace(".", ""))
            item["operator"] = "PCSC"
            item["operator_wikidata"] = "Q4642867"
            apply_category(Categories.SHOP_CONVENIENCE, item)
            if services := location.get("StoreImageTitle"):
                apply_yes_no(Extras.TOILETS, item, "廁所" in services)
                apply_yes_no(Extras.ATM, item, "ATM" in services)
                apply_yes_no(Extras.WIFI, item, "WiFi" in services)
            yield item
