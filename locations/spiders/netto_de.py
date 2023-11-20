import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Mo.": "Mo",
    "Di.": "Tu",
    "Mi.": "We",
    "Do.": "Th",
    "Fr.": "Fr",
    "Sa.": "Sa",
    "So.": "Su",
}


class NettoDESpider(scrapy.Spider):
    name = "netto_de"
    NETTO_CITY = {"brand": "Netto City", "brand_wikidata": "Q879858", "extras": Categories.SHOP_SUPERMARKET.value}
    NETTO_GETRANKE = {
        "brand": "Netto Getränke-Discount",
        "brand_wikidata": "Q879858",
        "extras": Categories.SHOP_BEVERAGES.value,
    }
    NETTO_MARKEN = {
        "brand": "Netto Marken-Discount",
        "brand_wikidata": "Q879858",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    item_attributes = NETTO_MARKEN
    allowed_domains = ["netto-online.de"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield scrapy.http.FormRequest(
            url="https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewNettoStoreFinder-GetStoreItems",
            formdata={
                "n": "56.0",
                "e": "15.0",
                "w": "5.0",
                "s": "47.0",
                "netto": "false",
                "city": "false",
                "service": "false",
                "beverage": "false",
                "nonfood": "false",
            },
        )

    def parse_opening_hours(self, hours):
        days_with_dot = list(DAY_MAPPING.keys())

        opening_hours = OpeningHours()
        for block in hours.split("<br />"):
            if not block:
                continue
            try:
                days, hrs = block.split(":")
                if hrs.strip().lower() == "geschlossen":
                    continue
                if "-" in days:
                    start_day, end_day = days.split("-")
                else:
                    start_day, end_day = days, days
                for day in days_with_dot[days_with_dot.index(start_day) : days_with_dot.index(end_day) + 1]:
                    open_time, close_time = hrs.split("-")
                    close_time = close_time.replace("Uhr", "").strip()
                    open_time = open_time.strip()
                    if open_time == "24.00":
                        open_time = "23.59"
                    if close_time == "24.00":
                        close_time = "23.59"
                    opening_hours.add_range(
                        day=DAY_MAPPING[day],
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H.%M",
                    )
            except:
                pass
        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()["store_items"]

        for store in stores:
            properties = {
                "ref": store["store_id"],
                "name": store["store_name"],
                "brand": store["store_name"],
                "street_address": store["street"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["post_code"],
                "lat": store["coord_latitude"],
                "lon": store["coord_longitude"],
                "website": "https://www.netto-online.de/filialen/{city}/{street}/{id}".format(
                    city=self.urlify(store["city"].lower()),
                    street=self.urlify(store["street"]),
                    id=store["store_id"],
                ),
            }

            if store["store_name"] == "Netto City":
                properties.update(self.NETTO_CITY)
            elif store["store_name"] == "Netto Getränke-Discount":
                properties.update(self.NETTO_GETRANKE)
            elif store["store_name"] == "Netto Marken-Discount":
                properties.update(self.NETTO_MARKEN)
            else:
                properties["brand"] = store["store_name"]
                self.crawler.stats.inc_value(f'atp/netto_de/unmapped_brand/{store["store_name"]}')

            properties["opening_hours"] = self.parse_opening_hours(store["store_opening"])

            yield Feature(**properties)

    def urlify(self, param):
        # They also do ß -> ss, but it's not vital
        return param.lower().replace(" ", "-").replace(".", "").replace(",", "").replace("'", "")
