# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class HangerclinicSpider(scrapy.Spider):
    name = "hangerclinic"
    item_attributes = {"brand": "Hanger Clinic"}
    allowed_domains = ["hangerclinic.com"]
    start_urls = ("http://www.hangerclinic.com/locations/Pages/by-state.aspx",)

    def format_hours(self, datestring):
        split_date = datestring.replace(";", ",").split(",")

        if "ppointment" in datestring:
            return "By Appointment"

        if len(split_date) == 2:
            matches = re.search(r"([\d]{1,2}).*?-.*?(\d{1,2})", split_date[1])

            if matches:

                def fmt_hr(hour):
                    hour = str(hour)

                    if len(hour) == 1:
                        hour = "0" + hour + ":00"
                    elif len(hour) == 2:
                        hour = hour + ":00"
                    elif len(hour) == 4:
                        hour = "0" + hour
                    return hour

                try:
                    am = int(matches.group(1))
                    pm = int(matches.group(2))

                    if pm != 12:
                        pm = int(pm) + 12
                except:
                    return

                hourstring = fmt_hr(am) + "-" + fmt_hr(pm)
                datestring = str(split_date[0]) + ", " + hourstring

        day_dict = {
            "Mon": "Mo",
            "Tue": "Tu",
            "Wed": "We",
            "Thu": "Th",
            "Fri": "Fr",
            "Sat": "Sa",
            "Sun": "Su",
            "Monday": "Mo",
            "Tuesday": "Tu",
            "Wednesday": "We",
            "Thursday": "Th",
            "Thurs": "Th",
            "Thur": "Th",
            "Friday": "Fr",
            "Saturday": "Sa",
            "Sunday": "Su",
            "24 hours/7 days a week": "24/7",
            "Please contact store for hours": "N/A",
            "Open only on": "",
            "Only": "",
            "A.M.": "",
            "P.M.": "",
        }
        pattern = re.compile(r"\b(" + "|".join(day_dict.keys()) + r")\b")
        datestring = pattern.sub(
            lambda x: day_dict[x.group()], datestring.replace(" - ", "-")
        )

        return datestring

    def parse(self, response):
        states = response.xpath(
            "//select[@class='locationsByStateSelect']/option/text()"
        )

        for state in states:
            link = (
                "http://www.hangerclinic.com/locations/Pages/by-state.aspx?state="
                + state.extract()
            )
            request = scrapy.Request(link, callback=self.parse_state)
            yield request

    def parse_state(self, response):
        store_links = response.xpath("//td[@class='byStateLocation']/a/@href")

        for link in store_links:
            store_link = "http://www.hangerclinic.com" + link.extract()
            store_link_request = scrapy.Request(store_link, callback=self.parse_store)
            yield store_link_request

    def parse_store(self, response):
        store_info = response.xpath("//div[@class='intro']")
        city, statezip = (
            store_info.xpath("//span[@id='locCityState']/text()")
            .extract()[0]
            .replace(" ", "")
            .replace("\n", "")
            .replace("\r", "")
            .split(",")
        )
        opening_hours = (
            store_info.xpath("//div[@id='locHours']/span[@class='locContent']/text()")
            .extract()[0]
            .strip()
        )
        street = store_info.xpath("//span[@id='locStreet']/text()").extract()[0].strip()

        properties = {
            "name": street.replace(" ", "_").replace(",", ""),
            "addr_full": street + ", " + city + " " + statezip[:2] + " " + statezip[2:],
            "ref": city + "_" + street.replace(" ", "_").replace(",", ""),
            "street": street.split(",")[0],
            "city": city,
            "state": statezip[:2],
            "postcode": statezip[2:],
            "opening_hours": self.format_hours(opening_hours),
            "phone": store_info.xpath(
                "//div[@id='locPhone']/span[@class='locContent']/text()"
            )
            .extract()[0]
            .strip(),
            "lat": float(
                store_info.xpath("//div[@id='locLat']/text()").extract()[0].strip()
            ),
            "lon": float(
                store_info.xpath("//div[@id='locLong']/text()").extract()[0].strip()
            ),
        }

        yield (GeojsonPointItem(**properties))
