import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class HeronFoodsSpider(scrapy.Spider):
    name = "heron_foods"
    item_attributes = {"brand": "Heron Foods", "brand_wikidata": "Q5743472"}
    allowed_domains = ["heronfoods.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield scrapy.FormRequest(
            url="https://heronfoods.com/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_stores",
                "lat": "51.5072178",
                "lng": "-0.1275862",
                "radius": "600",
            },
            callback=self.parse,
            headers={"Referer": "https://heronfoods.com/storelocator/"},
        )

    def parse(self, response):
        stores = response.json()
        for i in range(0, len(stores)):
            store = stores[str(i)]

            oh = OpeningHours()
            oh.add_range("Mo", store["op"]["0"].replace(".", ":"), store["op"]["1"].replace(".", ":"))
            oh.add_range("Tu", store["op"]["2"].replace(".", ":"), store["op"]["3"].replace(".", ":"))
            oh.add_range("We", store["op"]["4"].replace(".", ":"), store["op"]["5"].replace(".", ":"))
            oh.add_range(
                "Th",
                store["op"]["6"].replace(".", ":"),
                store["op"]["7"].replace(".", ":").replace("17:20:00", "17:20"),
            )
            oh.add_range("Fr", store["op"]["8"].replace(".", ":"), store["op"]["9"].replace(".", ":"))
            oh.add_range("Sa", store["op"]["10"].replace(".", ":"), store["op"]["11"].replace(".", ":"))
            oh.add_range("Su", store["op"]["12"].replace(".", ":"), store["op"]["13"].replace(".", ":"))

            properties = {
                "lat": store["lat"],
                "lon": store["lng"],
                "name": store["na"],
                "street_address": store["st"].strip(" ,"),
                "city": store["ct"].strip(),
                "postcode": store["zp"].strip(),
                "country": "GB",
                "website": store["gu"],
                "opening_hours": oh.as_opening_hours(),
                "ref": store["ID"],
            }
            if properties["name"].endswith(" (B&M Express)"):
                properties["name"] = properties["name"].replace(" (B&M Express)", "")
                properties["brand"] = "B&M Express"
                properties["brand_wikidata"] = "Q99640578"

            yield Feature(**properties)
