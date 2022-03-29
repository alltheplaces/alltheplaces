import json
import scrapy

from locations.items import GeojsonPointItem

day_formats = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class HugoBossSpider(scrapy.Spider):
    name = "hugoboss"
    item_attributes = {"brand": "Hugo Boss"}
    allowed_domains = ["production-web-hugo.demandware.net"]
    download_delay = 0.5
    start_urls = (
        "https://production-web-hugo.demandware.net/s/US/dw/shop/v16_9/stores?client_id=871c988f-3549-4d76-b200-8e33df5b45ba&latitude=37.09024&longitude=-95.71289100000001&count=200&maxDistance=100000000&distanceUnit=mi",
    )
    count = 0

    def parse(self, response):
        data = response.json()
        if "data" in data:
            for store in data["data"]:
                clean_hours = ""
                if "store_hours" in store:
                    open_hours = json.loads(store["store_hours"])
                    for key, value in open_hours.items():
                        if isinstance(value[0], str):
                            clean_hours = (
                                clean_hours
                                + day_formats[key]
                                + " "
                                + value[0]
                                + "-"
                                + value[1]
                                + "; "
                            )
                        else:
                            clean_hours = (
                                clean_hours
                                + day_formats[key]
                                + " "
                                + value[0][0]
                                + "-"
                                + value[0][1]
                                + "; "
                            )
                if "postal_code" in store:
                    postal_code = store["postal_code"]
                else:
                    postal_code = ""
                if "phone" in store:
                    phone = store["phone"]
                else:
                    phone = ""
                properties = {
                    "ref": store["id"],
                    "name": store["name"],
                    "opening_hours": clean_hours,
                    "website": "https://www.hugoboss.com/us/stores",
                    "addr_full": store["address1"],
                    "city": store["city"],
                    "postcode": postal_code,
                    "country": store["country_code"],
                    "lat": float(store["latitude"]),
                    "lon": float(store["longitude"]),
                    "phone": phone,
                }

                yield GeojsonPointItem(**properties)
            self.count = self.count + len(data["data"])
            yield scrapy.Request(
                response.urljoin(self.start_urls[0] + "&start=" + str(self.count)),
                callback=self.parse,
            )
