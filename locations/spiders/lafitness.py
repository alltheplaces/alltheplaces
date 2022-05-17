import datetime
import scrapy
import re
import json

from locations.items import GeojsonPointItem


DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class LAFitnessSpider(scrapy.Spider):
    name = "lafitness"
    item_attributes = {"brand": "LA Fitness", "brand_wikidata": "Q6457180"}
    allowed_domains = ["lafitness.com"]
    download_delay = 0.1

    def start_requests(self):
        data = {"zipCode": None, "state": None}
        yield scrapy.Request(
            url="https://www.lafitness.com/Pages/GetClubLocations.aspx/GetClubLocationsByStateAndZipCode",
            method="POST",
            body=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

    def parse_hours(self, elems):
        opening_hours = []

        hours = elems.xpath(".//text()").extract()

        if not hours:
            return None

        hours.pop(hours.index("CLUB HOURS"))

        hours = list(zip(hours[0::2], hours[1::2]))
        for hour in hours:
            if (hour[0] == "Mon - Sun") & (hour[1] == "24 Hours Open"):
                return "24/7"

            try:
                open_time, close_time = re.search(
                    r"(.*)\s-\s(.*)", hour[1], re.IGNORECASE
                ).groups()
            except:
                if hour[1] == "24 Hours Open":
                    open_time, close_time = "12:00am", "11:59pm"
                else:
                    raise
            if close_time == "Midnight":
                close_time = "12:00am"
            if open_time == "Midnight":
                open_time = "12:00am"

            open_time = datetime.datetime.strptime(open_time, "%I:%M%p").strftime(
                "%H:%M"
            )
            close_time = datetime.datetime.strptime(close_time, "%I:%M%p").strftime(
                "%H:%M"
            )

            day_range = re.search(r"([a-z]{3})\s-\s([a-z]{3})", hour[0], re.IGNORECASE)
            if day_range:
                day_start, day_end = day_range.groups()
                opening_hours.append(
                    "{}-{} {}-{}".format(
                        DAY_MAPPING[day_start],
                        DAY_MAPPING[day_end],
                        open_time,
                        close_time,
                    )
                )
            else:
                opening_hours.append(
                    "{} {}-{}".format(DAY_MAPPING[hour[0]], open_time, close_time)
                )

        return ";".join(opening_hours)

    def parse_club(self, response):
        properties = response.meta["properties"]

        properties.update(
            {
                "phone": response.xpath(
                    '//span[contains(@id, "lblClubPhone")]/text()'
                ).extract_first(),
                "addr_full": response.xpath(
                    '//span[contains(@id, "lblClubAddress")]/text()'
                ).extract_first(),
                "city": response.xpath(
                    '//span[contains(@id, "lblClubCity")]/text()'
                ).extract_first(),
                "state": response.xpath(
                    '//span[contains(@id, "lblClubState")]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//span[contains(@id, "lblZipCode")]/text()'
                ).extract_first(),
                "website": response.url,
            }
        )

        opening_hours = self.parse_hours(
            response.xpath('//div[@id="divClubHourPanel"]//tr')
        )

        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        locations = response.json()["d"]

        for location in locations:

            properties = {
                "name": location["Description"],
                "ref": location["ClubID"],
                "lat": float(location["Latitude"]),
                "lon": float(location["Longitude"]),
            }

            yield scrapy.Request(
                "https://www.lafitness.com/pages/" + location["ClubHomeURL"],
                callback=self.parse_club,
                meta={"properties": properties},
            )
