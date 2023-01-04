import scrapy
import xmltodict

from datetime import datetime

from locations.items import GeojsonPointItem
from locations.hours import DAYS_EN, OpeningHours

class ChemistWarehouseSpider(scrapy.Spider):
    name = "chemist_warehouse_au"
    item_attributes = {"brand": "Chemist Warehouse", "brand_wikidata": "Q48782120"}
    allowed_domains = ["www.chemistwarehouse.com.au"]
    start_urls = [
        "https://www.chemistwarehouse.com.au/ams/webparts/Google_Map_SL_files/storelocator_data.ashx?searchedPoint=(0,%200)&TrafficSource=1&TrafficSourceState=0"
    ]

    def parse(self, response):
        for data in xmltodict.parse(response.text).get("markers").get("marker"):
            item = GeojsonPointItem()
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
            for day in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
                open_hour_raw = data.get("@store" + day.lower()).split(" - ")[0].replace(".", ":")
                if "CLOSED" in open_hour_raw:
                    open_hour = "closed"
                elif open_hour_raw == "00:00AM":
                    open_hour = "00:00"
                else:
                    open_hour = datetime.strptime(open_hour_raw, "%I:%M%p").strftime("%H:%M")
                close_hour_raw = data.get("@store" + day.lower()).split(" - ")[1].replace(".", ":")
                if "CLOSED" in open_hour_raw:
                    close_hour = "closed"
                elif close_hour_raw == "00:00AM":
                    close_hour = "24:00"
                else:
                    close_hour = datetime.strptime(close_hour_raw, "%I:%M%p").strftime("%H:%M")
                oh.add_range(DAYS_EN[day], open_hour, close_hour)
            item["opening_hours"] = oh.as_opening_hours()

            yield item
