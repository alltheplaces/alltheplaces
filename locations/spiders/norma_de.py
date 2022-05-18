import scrapy
import csv
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class NormaDeSpider(scrapy.Spider):
    name = "norma_de"
    item_attributes = {"brand": "Norma", "brand_wikidata": "Q450180"}
    allowed_domains = ["www.norma-online.de"]

    start_urls = []
    with open(
        "./locations/searchable_points/germany_centroids_80km_radius_country.csv"
    ) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        for row in csv_reader:
            if row[4] == "Germany":
                start_urls.append(
                    f"https://www.norma-online.de/de/filialfinder"
                    f"/suchergebnis?lng={row[3]}&lat={row[2]}&r=80000"
                )

    download_delay = 0.2

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("dayOfWeek")]
            open_time = store_day.get("fromTime")
            close_time = store_day.get("toTime")
            if open_time is None and close_time is None:
                continue
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse_hours(self, store):
        opening_hours = OpeningHours()
        try:
            weekday = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]'
                '//table[@class="shopHours"]//tbody//tr//td/text()'
            )[0].get()
            if weekday:
                from_tm, to_tm = weekday.replace(" ", "").split("-")
                for day in ["Mo", "Tu", "We", "Th", "Fr"]:
                    opening_hours.add_range(
                        day=day,
                        open_time=from_tm.strip(),
                        close_time=to_tm.strip(),
                        time_format="%H:%M",
                    )
        except IndexError:
            pass

        try:
            weekday = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]'
            )[1].get()
            match = re.search(r"Pon.*?: (\d+:\d+) - (\d+:\d+)", weekday)
            if match:
                for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                    opening_hours.add_range(
                        day=day,
                        open_time=match.group(1).strip(),
                        close_time=match.group(2).strip(),
                        time_format="%H:%M",
                    )
        except IndexError:
            pass

        try:
            saturday = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]'
                '//table[@class="shopHours"]//tbody//tr//td/text()'
            )[1].get()
            if saturday:
                from_tm, to_tm = saturday.replace(" ", "").split("-")
                opening_hours.add_range(
                    day="Sa",
                    open_time=from_tm.strip(),
                    close_time=to_tm.strip(),
                    time_format="%H:%M",
                )
        except IndexError:
            pass

        return opening_hours.as_opening_hours()

    def parse(self, response):
        for store in response.xpath('//div[@class="item"]//div[@class="row"]'):
            street = city = zip = lat = lon = ""

            address = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]//p'
            ).get()
            match = re.search(r"<p>(.*?)<br>", address)
            if match:
                street = match.group(1)

            match = re.search(r"(\d{5}) (.*?)<\/p>", address)
            if match:
                zip = match.group(1)
                city = match.group(2)

            position = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-2 col-lg-2 actions"]'
                "//a/@href"
            ).get()
            if position:
                match = re.search(r"lng=(.*?)&lat=(.*?)&", position)
                if match:
                    lat = match.group(2)
                    lon = match.group(1)

            properties = {
                "ref": f"{lat}_{lon}",
                "street": street,
                "city": city,
                "postcode": zip,
                "country": "DE",
                "lat": lat,
                "lon": lon,
            }

            hours = self.parse_hours(store)
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
