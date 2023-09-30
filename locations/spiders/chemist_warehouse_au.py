import scrapy
import xmltodict

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class ChemistWarehouseAUSpider(scrapy.Spider):
    name = "chemist_warehouse_au"
    item_attributes = {"brand": "Chemist Warehouse", "brand_wikidata": "Q48782120"}
    allowed_domains = ["www.chemistwarehouse.com.au"]
    start_urls = [
        "https://www.chemistwarehouse.com.au/ams/webparts/Google_Map_SL_files/storelocator_data.ashx?searchedPoint=(0,%200)&TrafficSource=1&TrafficSourceState=0"
    ]
    requires_proxy = True  # Residential IP addresses appear to be required.

    def parse(self, response):
        for data in xmltodict.parse(response.text).get("markers").get("marker"):
            item = Feature()
            item["ref"] = data.get("@id")
            item["name"] = data.get("@storename")
            item["lat"] = data.get("@lat")
            item["lon"] = data.get("@lng")
            item["street_address"] = " ".join(data.get("@storeaddress").split())
            item["city"] = data.get("@storesuburb")
            item["state"] = data.get("@storestate")
            item["postcode"] = data.get("@storepostcode")
            item["country"] = "AU"
            item["phone"] = data.get("@storephone")
            item["email"] = data.get("@storeemail")
            oh = OpeningHours()
            for day in DAYS_FULL:
                rule = (
                    data["@store" + day[:3].lower()].replace(".", ":").replace("00:00AM - 00:00AM", "12:00AM - 12:00AM")
                )
                open_time, close_time = rule.split(" - ")
                if open_time == "0" or close_time == "0":
                    continue
                oh.add_range(day, open_time, close_time, time_format="%I:%M%p")
            item["opening_hours"] = oh.as_opening_hours()

            yield item
