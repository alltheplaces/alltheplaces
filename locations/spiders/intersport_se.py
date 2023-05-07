import unicodedata

import scrapy

from locations.hours import DAYS_EN, DAYS_FULL, NAMED_DAY_RANGES_EN, OpeningHours
from locations.items import Feature


class IntersportSESpider(scrapy.Spider):
    name = "intersport_se"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.se/api/v2/stores/limited/"]

    def parse(self, response):
        response.selector.remove_namespaces()
        stores = response.xpath("/ArrayOfLimitedStore/LimitedStore")
        for store in stores:
            # There is a StoreNo but there is no more info.
            # ref = store.xpath("./StoreNo/text()").get()
            ref = self.get_website(store.xpath("./StoreName/text()").get())
            name = "Intersport " + store.xpath("./StoreName/text()").get()
            city = store.xpath("./VisitCity/text()").get()
            lon = float(store.xpath("./Longitude/text()").get())
            lat = float(store.xpath("./Latitude/text()").get())
            opening_hours = self.parse_hours(store)
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

    def get_website(self, store_name):
        # from this page you can find out the pattern in the website name by looking at the different links.
        # https://www.intersport.se/vara-butiker/
        url_prefix = "https://www.intersport.se/vara-butiker/"
        return url_prefix + "-".join(self.remove_accent(store_name).split(" ")).lower()

    def add_website_info(self, response, properties):
        addr_full = response.xpath('//*[@class="m-b-mini"][2]/text()').get()
        street_address = addr_full.rsplit(",", maxsplit=1)[0]
        street = street_address.split(" ")[0]
        postcode = addr_full.split(",")[-1].split(" ")[1]
        phone = response.xpath('//*[@class="font-medium m-b-mini"]/*[@data-am-link="primary underline"]/text()').get()
        email = response.xpath('//*[@class="font-medium m-b"]/*[@data-am-link="primary underline"]/text()').get()

        properties["addr_full"] = addr_full
        properties["street_address"] = street_address
        properties["street"] = street
        properties["postcode"] = postcode
        properties["phone"] = phone
        properties["email"] = email

        yield Feature(**properties)

    def parse_hours(self, store):
        open_hours_path = store.xpath("./OpenHours/RegularHours")
        opening_hours = OpeningHours()
        if (hours := open_hours_path.xpath("./Weekday/text()").get()) is not None:
            # Add Week days
            open_time, close_time = hours.split("-")
            opening_hours.add_days_range(
                days=NAMED_DAY_RANGES_EN["Weekdays"], open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

            # Adds weekend
            for day in ["Saturday", "Sunday"]:
                day_hours = open_hours_path.xpath(f"./{day}/text()").get()
                if day_hours is not None:
                    open_hours, close_hours = day_hours.split("-")
                    opening_hours.add_range(day="Sa", open_time=open_hours, close_time=close_hours, time_format="%H:%M")
        else:
            for day in DAYS_FULL:
                hours = open_hours_path.xpath(f"./{day}/text()").get()
                if hours:
                    open_time, close_time = hours.split("-")
                    opening_hours.add_range(
                        day=DAYS_EN[day], open_time=open_time, close_time=close_time, time_format="%H:%M"
                    )

        return opening_hours.as_opening_hours()

    def remove_accent(self, value):
        """
        Remove accent from text
        :param value: value to remove accent from
        :return: value without accent
        """
        return unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode("utf-8", "ignore")
