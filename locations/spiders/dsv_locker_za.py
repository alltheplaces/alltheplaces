from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DsvLockerZASpider(Spider):
    name = "dsv_locker_za"
    item_attributes = {"brand": "DSV Locker", "brand_wikidata": "Q1155771"}
    allowed_domains = ["dsv-clientzone-map.afrigis.co.za"]
    start_urls = ["https://dsv-clientzone-map.afrigis.co.za/proxy/api/wfs/?layer=locker"]

    def parse(self, response):
        for data in response.json()["result"]["features"]:
            data = data["properties"]
            item = DictParser.parse(data)
            item["ref"] = data.get("location_code")
            item["name"] = data.get("location_name")
            item["lat"] = data.get("gps_latitude")
            item["lon"] = data.get("gps_longitude")
            item["phone"] = data.get("contact_dsv_tel")
            item["email"] = data.get("contact_dsv_email")
            item["city"] = data["suburb"]

            item["opening_hours"] = OpeningHours()

            if opening_hours := data.get("business_hours"):
                item["opening_hours"].add_ranges_from_string(opening_hours.replace("24/7", "00:00-24:00"))

            yield item
