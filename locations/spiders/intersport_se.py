import unicodedata

import scrapy

from locations.hours import DAYS, DAYS_FULL, NAMED_DAY_RANGES_EN, OpeningHours
from locations.items import Feature


class IntersportSESpider(scrapy.Spider):
    name = "intersport_se"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.se/api/v2/stores/limited/"]

    def parse(self, response):
        response.selector.remove_namespaces()
        stores = response.xpath("/ArrayOfLimitedStore/LimitedStore")
        for store in stores:
            ref = store.xpath("./StoreNo/text()").get()
            name = "Intersport " + store.xpath("./StoreName/text()").get()
            city = store.xpath("./VisitCity/text()").get()
            lon = float(store.xpath("./Longitude/text()").get())
            lat = float(store.xpath("./Latitude/text()").get())
            opening_hours = self.parse_hours(store.xpath("./OpenHours/RegularHours"))
            website = self.get_website(store.xpath("./StoreName/text()").get())

            properties = {
                "ref": ref,
                "name": name,
                "city": city,
                "lon": lon,
                "lat": lat,
                "opening_hours": opening_hours,
                "website": website,
            }

            if website:
                yield scrapy.http.Request(
                    url=website,
                    method="GET",
                    callback=self.add_website_info,
                    cb_kwargs={"properties": properties},
                )
            else:
                yield Feature(**properties)

    def add_website_info(self, response, properties):
        addr_full = response.xpath(
            '//*[@id="server-side-container"]/div[2]/div/div[1]/div/div[2]/div[1]/div[2]/text()'
        ).get()
        street_address = addr_full.rsplit(",", maxsplit=1)[0]
        street = street_address.split(" ")[0]
        postcode = addr_full.split(",")[-1].split(" ")[1]
        phone = response.xpath('//*[@id="server-side-container"]/div[2]/div/div[1]/div/div[2]/div[2]/a/text()').get()
        email = response.xpath('//*[@id="server-side-container"]/div[2]/div/div[1]/div/div[2]/div[3]/a/text()').get()

        properties["addr_full"] = addr_full
        properties["street_address"] = street_address
        properties["street"] = street
        properties["postcode"] = postcode
        properties["phone"] = phone
        properties["email"] = email

        yield Feature(**properties)

    def get_website(self, store_name):
        # from this page you can find out the pattern in the website name by looking at the different links.
        # https://www.intersport.se/vara-butiker/
        url_prefix = "https://www.intersport.se/vara-butiker/"
        return url_prefix + "-".join(self.remove_accent(store_name).split(" ")).lower()

    def parse_hours(self, open_hours):
        opening_hours = OpeningHours()
        if open_hours.xpath("./Weekday/text()").get() is not None:
            # Add Week days
            hours = open_hours.xpath("./Weekday/text()").get()
            open_time, close_time = hours.split("-")
            opening_hours.add_days_range(
                days=NAMED_DAY_RANGES_EN["Weekdays"], open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

            # Adds weekend
            saturday = open_hours.xpath("./Saturday/text()").get()
            if saturday is not None:
                saturday_open, saturday_close = saturday.split("-")
                opening_hours.add_range(
                    day="Sa", open_time=saturday_open, close_time=saturday_close, time_format="%H:%M"
                )

            sunday = open_hours.xpath("./Sunday/text()").get()
            if sunday is not None:
                sunday_open, sunday_close = sunday.split("-")
                opening_hours.add_range(day="Su", open_time=sunday_open, close_time=sunday_close, time_format="%H:%M")

        else:
            for full_day, day in zip(DAYS_FULL, DAYS):
                hours = open_hours.xpath(f"./{full_day}/text()").get()
                if hours:
                    open_time, close_time = hours.split("-")
                    opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def remove_accent(self, value):
        """
        Remove accent from text
        :param value: value to remove accent from
        :return: value without accent
        """
        return unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode("utf-8", "ignore")
