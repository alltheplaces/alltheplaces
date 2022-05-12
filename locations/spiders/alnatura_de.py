import scrapy
import re
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    1: "Mo",
    2: "Tu",
    3: "We",
    4: "Th",
    5: "Fr",
    6: "Sa",
    7: "Su",
    "Mo": 1,
    "Tu": 2,
    "We": 3,
    "Th": 4,
    "Fr": 5,
    "Sa": 6,
    "Su": 7,
}


class AlnaturaSpider(scrapy.Spider):
    name = "alnatura_de"
    item_attributes = {"brand": "Alnatura", "brand_wikidata": "Q876811"}
    allowed_domains = ["www.alnatura.de"]
    start_urls = (
        "https://www.alnatura.de/api/sitecore/stores/FindStoresforMap?"
        "ElementsPerPage=10000&lat=50.99820058296841"
        "&lng=7.811966062500009&radius=1483"
        "&Tradepartner=Alnatura%20Super%20Natur%20Markt",
    )
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        match = re.match(r"(.+?)-(.+?) +(\d.*?)-(.+?) Uhr", store_hours)
        if match:
            from_day = match.group(1).strip()
            to_day = match.group(2).strip()
            from_time = match.group(3).strip().replace(":", ".")
            to_time = match.group(4).strip().replace(":", ".")

            fhours = int(float(from_time))
            fminutes = (float(from_time) * 60) % 60
            fmt_from_time = "%d:%02d" % (fhours, fminutes)
            thours = int(float(to_time))
            tminutes = (float(to_time) * 60) % 60
            fmt_to_time = "%d:%02d" % (thours, tminutes)

            for day in range(DAY_MAPPING[from_day], DAY_MAPPING[to_day] + 1):
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=fmt_from_time,
                    close_time=fmt_to_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        store = json.loads(response.text)
        store = store["Payload"]

        properties = {
            "lat": response.meta.get("lat"),
            "lon": response.meta.get("lng"),
            "name": store["StoreName"],
            "street": store["Street"],
            "city": store["City"],
            "postcode": store["PostalCode"],
            "phone": store["Tel"],
            "country": store["Country"],
            "ref": response.meta.get("id"),
        }

        if store["OpeningTime"]:
            hours = self.parse_hours(store.get("OpeningTime"))
            if hours:
                properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        data = json.loads(response.text)

        for stores in data["Payload"]:
            yield scrapy.Request(
                f"https://www.alnatura.de/api/sitecore/stores/StoreDetails"
                f"?storeid={stores['Id']}",
                callback=self.parse_stores,
                meta={
                    "lat": stores["Lat"].replace(",", "."),
                    "lng": stores["Lng"].replace(",", "."),
                    "id": stores["Id"],
                },
            )
