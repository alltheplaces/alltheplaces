# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem
from scrapy.selector import Selector


def opening_hours(datestring):
    hour_match = re.findall(r"(\d{1,2}:\d{1,2}.(am|pm|-)|\d{1,2}(am|pm))", datestring)
    hours = [str(i[0]) for i in hour_match]

    try:
        hours = [str(i[0]) for i in hour_match]
        mil_hrs = list(hours)
    except:
        pass

    if mil_hrs:
        for i in range(len(mil_hrs)):
            hour = mil_hrs[i]
            hour = re.sub(r"[AaMm]{2}", "", hour.replace("-", ""))

            if re.search(r"[PpMm]{2}", hour) is not None:
                hour = re.sub(r"[PpMm]{2}", "", hour)
                hour = hour.replace(":", ".")
                hour = "%.2f" % (float(hour) + 12)
                hour = hour.replace(".", ":")

            if len(hour) == 1:
                hour = "0" + hour + ":00"
            elif len(hour) == 2:
                hour = hour + ":00"
            elif len(hour) == 4:
                hour = "0" + hour

            mil_hrs[i] = hour

        first = datestring.split(hours[0])[0]
        second = ""
        third = ""
        fourth = ""
        opening_hours = ""

        try:
            regex = str("(?<=" + hours[1] + ")(.*?)(?=" + hours[2] + ")")
            second = ((re.search(regex, datestring)).group(0)).lstrip()
            regex = str("(?<=" + hours[3] + ")(.*?)(?=" + hours[4] + ")")
            third = ((re.search(regex, datestring)).group(0)).lstrip()
            regex = str(hours[5] + "(?!.*" + hours[5] + ")(.*?)(?=" + hours[6] + ")")
            fourth = ((re.search(regex, datestring)).group(1)).lstrip()

        except:
            pass

        for i in range(8):
            try:
                mil_hrs[i]
            except:
                mil_hrs.append("")

        def fmt(period, first=0):
            if period != "":
                if not first:
                    period = ", " + period
            period = (
                period.replace(" - ", "-")
                .replace(" -", "-")
                .replace(".", "")
                .replace(":", " ")
                .replace("  ", " ")
            )
            return period

        def hours(a, b):
            if a == "" or b == "":
                return ""
            else:
                return a + "-" + b

        strings = [
            fmt(first, 1),
            hours(mil_hrs[0], mil_hrs[1]),
            fmt(second),
            hours(mil_hrs[2], mil_hrs[3]),
            fmt(third),
            hours(mil_hrs[4], mil_hrs[5]),
            fmt(fourth),
            hours(mil_hrs[6], mil_hrs[7]),
        ]
        opening_hours = "".join(filter(None, strings))

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
        }
        pattern = re.compile(r"\b(" + "|".join(day_dict.keys()) + r")\b")
        opening_hours = pattern.sub(
            lambda x: day_dict[x.group()], "".join(opening_hours)
        )

        return opening_hours.title()


class KeyfoodSpider(scrapy.Spider):
    name = "keyfood"
    item_attributes = {"brand": "Key Food"}
    allowed_domains = ["keyfood.mywebgrocer.com"]
    start_urls = ("http://keyfood.mywebgrocer.com/StoreLocator.aspx",)

    def parse(self, response):
        states = ["CT", "NJ", "NY", "PA"]

        for state in states:
            yield scrapy.FormRequest.from_response(
                response=response,
                formdata={
                    "postBack": "1",
                    "action": "GL",
                    "stateSelIndex": "",
                    "citySelIndex": "",
                    "selStates": state,
                    "selCities": "",
                    "txtZipCode": "",
                    "selZipCodeRadius": "5",
                },
                clickdata={"class": "submitButton"},
                dont_filter=True,
                callback=self.parse_state,
            )

    def parse_state(self, response):
        stores = response.css("div.StoreBox")

        for store in stores:
            name = store.css(".StoreTitle").xpath("text()").extract()
            address = store.css(".StoreAddress p").xpath("text()").extract()
            address1 = address[0]
            address2 = address[len(address) - 1].split(",")
            store_hours = store.css(".StoreHours p.tInfo").xpath("text()").extract()
            phone = store.css(".StoreContact p.tInfo").xpath("text()").extract()
            latlon = str(store.css("a.SingleItemLinkText").extract())
            latlon = (re.search('ll=(.*)0"', latlon)).group(1)
            lat, lon = latlon.split(",")

            properties = {
                "name": "".join(name),
                "ref": "".join(name)
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "_"),
                "street": address1,
                "city": address2[0],
                "state": address2[1].split(" ")[1],
                "postcode": address2[1].split(" ")[2],
                "opening_hours": opening_hours("".join(store_hours)),
                "phone": "".join(phone)[7:],
                "lat": float(lat),
                "lon": float(lon),
            }

            yield GeojsonPointItem(**properties)
