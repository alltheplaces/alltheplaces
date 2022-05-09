# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

regex_am = r"\s?([Aa][Mm])"
regex_pm = r"\s?([Pp][Mm])"
regex_hours = (
    r"\d{1,2}:\d{1,2}\s?[Aa]?[Pp]?[Mm]\s?-\s?\d{1,2}:\d{1,2}\s?" r"[Aa]?[Pp]?[Mm]"
)


class BcpizzaSpider(scrapy.Spider):
    name = "bcpizza"
    item_attributes = {"brand": "BC Pizza"}
    allowed_domains = ["bc.pizza"]
    start_urls = [
        "https://bc.pizza/wp-admin/admin-ajax.php?action=store_search&lat=42.331427&lng=-83.0457538&max_results=100&search_radius=1000&_=1515354445197"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def convert_hours(self, hours):
        hours = [x.strip() for x in hours]
        hours = [x for x in hours if x]
        for i in range(len(hours)):
            converted_times = ""
            if hours[i] != "Closed":
                if hours[i] != "Open 24 Hours":
                    from_hr, to_hr = [hr.strip() for hr in hours[i].split("-")]
                    if re.search(regex_am, from_hr):
                        from_hr = re.sub(regex_am, "", from_hr)
                        hour_min = from_hr.split(":")
                        if len(hour_min[0]) < 2:
                            hour_min[0].zfill(2)
                        converted_times += (":".join(hour_min)) + "-"
                    else:
                        from_hr = re.sub(regex_pm, "", from_hr)
                        hour_min = from_hr.split(":")
                        if int(hour_min[0]) < 12:
                            hour_min[0] = str(12 + int(hour_min[0]))
                        converted_times += (":".join(hour_min)) + "-"

                    if re.search(regex_am, to_hr):
                        to_hr = re.sub(regex_am, "", to_hr)
                        hour_min = to_hr.split(":")
                        if len(hour_min[0]) < 2:
                            hour_min[0].zfill(2)
                        if int(hour_min[0]) == 12:
                            hour_min[0] = "00"
                        converted_times += ":".join(hour_min)
                    else:
                        to_hr = re.sub(regex_pm, "", to_hr)
                        hour_min = to_hr.split(":")
                        if int(hour_min[0]) < 12:
                            hour_min[0] = str(12 + int(hour_min[0]))
                        converted_times += ":".join(hour_min)
                else:
                    converted_times = "00:00-24:00"
            else:
                converted_times += "off"
            hours[i] = converted_times
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        hours = "".join("{} {} ".format(*t) for t in zip(days, hours))
        return hours

    def parse(self, response):
        results = response.json()
        for i in results:
            ref = i["id"]
            street = i["address"]
            city = i["city"]
            state = i["state"]
            postcode = i["zip"]
            lat = float(i["lat"])
            lon = float(i["lng"])
            hours = i["hours"]
            hours = self.convert_hours(re.findall(regex_hours, hours))
            phone = i["phone"]
            website = i["facebook_url"]
            addr_full = "{} {}, {} {}".format(street, city, state, postcode)

            yield GeojsonPointItem(
                ref=ref,
                street=street,
                city=city,
                state=state,
                postcode=postcode,
                addr_full=addr_full,
                lat=lat,
                lon=lon,
                phone=phone,
                website=website,
                opening_hours=hours,
            )
