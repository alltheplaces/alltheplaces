import scrapy
import xmltodict

from locations.hours import DAYS, OpeningHours
from locations.items import GeojsonPointItem


class LandsEndSpider(scrapy.Spider):
    name = "landsend"
    item_attributes = {"brand": "Lands' End", "brand_wikidata": "Q839555"}
    allowed_domains = ["landsend.com"]
    start_urls = [
        "https://www.landsend.com/pp/StoreLocator?lat=42.7456634&lng=-90.4879916&radius=3000&S=S&L=L&C=undefined&N=N"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        json_data = xmltodict.parse(response.text).get("markers", {}).get("marker")
        for store in json_data:
            openingHours = store.get("@storehours").replace(":", ": ").replace(" - ", "-").split()
            days = [openingHours[i] for i in range(0, len(openingHours), 2)]
            hours = [openingHours[i] for i in range(1, len(openingHours), 2)]
            openHourResult = []
            for j in range(len(openingHours) // 2):
                if hours[j] in ["CLOSED", "Closed"]:
                    continue
                if len(days[j].strip(":").split("-")) == 2:
                    start = [DAYS.index(row) for row in DAYS if row[:1] == days[j].strip(":").split("-")[0][0]][-1]
                    end = [DAYS.index(row) for row in DAYS if row[:1] == days[j].strip(":").split("-")[1][0]][-1]
                    openHourResult.extend(f"{DAYS[i]} {hours[j]}" for i in range(start, end + 1))
                else:
                    openHourResult.append(f"{days[j].strip(':')[:2]} {hours[j]}")

            oh = OpeningHours()
            oh.from_linked_data({"openingHours": openHourResult}, "%I")

            properties = {
                "ref": store.get("@storenumber"),
                "name": store.get("@name"),
                "street_address": store.get("@address"),
                "city": store.get("@city"),
                "state": store.get("@state"),
                "postcode": store.get("@zip"),
                "phone": store.get("@phonenumber"),
                "lat": store.get("@lat"),
                "lon": store.get("@lng"),
                "opening_hours": oh.as_opening_hours(),
            }

            yield GeojsonPointItem(**properties)
