import scrapy

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class ChiquitoSpider(scrapy.Spider):
    name = "chiquito"
    item_attributes = {"brand": "Chiquito", "brand_wikidata": "Q5101775"}
    allowed_domains = ["www.chiquito.co.uk"]
    start_urls = [
        "https://www.chiquito.co.uk/api/content/restaurants",
    ]

    def parse(self, response):
        stores = response.json()["restaurants"]["fields"]["list"]

        for store in stores:
            properties = {
                "lat": store["fields"]["latitude"],
                "lon": store["fields"]["longitude"],
                "ref": store["fields"]["siteId"],
                "name": store["fields"]["name"],
                "street_address": store["fields"]["street"],
                "city": store["fields"]["city"],
                "postcode": store["fields"]["postalCode"],
                "country": store["fields"]["country"].upper(),
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["fields"]["street"],
                            store["fields"]["city"],
                            store["fields"]["region"],
                            store["fields"]["postalCode"],
                            "United Kingdom",
                        ),
                    )
                ),
                "phone": "+44 " + store["fields"]["telephone"][1:],
                "website": "https://" + store["fields"]["url"],
                "extras": {
                    "delivery": "yes" if store["fields"]["enableDeliveries"] else "no",
                    "takeaway": "yes" if store["fields"]["enableClickAndCollect"] else "no",
                    "contact:deliveroo": store["fields"].get("deliverooDirectLink"),
                    "contact:uberEats": store["fields"].get("uberEatsDirectLink"),
                    "contact:justEat": store["fields"].get("justEatDirectLink"),
                },
            }
            oh = OpeningHours()

            for day in DAYS_FULL:
                open_time = self.parse_time(store["fields"]["open" + day].split("-")[0])
                close_time = self.parse_time(store["fields"]["open" + day].split("-")[1])

                oh.add_range(day, open_time, close_time, "%I:%M%p")

            properties["opening_hours"] = oh

            yield Feature(**properties)

    def parse_time(self, time):
        time = time.strip()
        if "." in time:
            time = time.replace(".", ":")

        if len(time) == 3:
            time = "0" + time
        if ":" not in time:
            time = time[0:2] + ":00" + time[2:]
        return time
