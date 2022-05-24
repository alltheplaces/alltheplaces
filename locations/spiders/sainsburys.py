import re
import scrapy
from locations.items import GeojsonPointItem

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class SainsburysSpider(scrapy.Spider):
    name = "sainsburys"
    item_attributes = {"brand": "Sainsbury's", "brand_wikidata": "Q152096"}
    allowed_domains = ["stores.sainsburys.co.uk"]
    state = True

    def start_requests(self):
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.kfc.com",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
            "Referer": "http://locator.safeway.com/sto…edirection=no&mylocation=2706",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        for page in range(1000):
            if self.state == False:
                break
            else:
                url = (
                    "https://stores.sainsburys.co.uk/api/v1/stores/?fields=slfe-list-2.21&api_client_id=slfe&lat=54.652247&lon=-2.219954&limit=25000000&store_type=main%2Clocal&sort=by_distance&within=1500000&page="
                    + str(page)
                )
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = response.json()

        if len(data["results"]) == 0:
            self.state = False
        else:
            for store in data["results"]:
                open_hours = store["opening_times"]
                clean_hours = ""
                for idx, time in enumerate(open_hours):
                    clean_hours = (
                        clean_hours
                        + DAYS[time["day"]]
                        + " "
                        + time["start_time"]
                        + "-"
                        + time["end_time"]
                        + " ; "
                    )

                properties = {
                    "ref": store["code"],
                    "name": store["name"],
                    "opening_hours": clean_hours,
                    "website": "https://stores.sainsburys.co.uk/%s/%s"
                    % (store["code"], store["other_name"].lower().replace(" ", "-")),
                    "addr_full": store["contact"]["address1"],
                    "city": store["contact"]["city"],
                    "postcode": store["contact"]["post_code"],
                    "country": "United Kingdom",
                    "lon": float(store["location"]["lon"]),
                    "lat": float(store["location"]["lat"]),
                }
                yield GeojsonPointItem(**properties)
