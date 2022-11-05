import re

import scrapy
from geonamescache import GeonamesCache

from locations.items import GeojsonPointItem

regex_am = r"\s?([Aa][Mm])"
regex_pm = r"\s?([Pp][Mm])"


class TacobuenoSpider(scrapy.Spider):
    name = "bueno"
    item_attributes = {
        "brand": "Taco Bueno",
        "brand_wikidata": "Q7673958",
        "country": "US",
    }
    allowed_domains = ["buenoonthego.com"]
    download_delay = 0.1

    def start_requests(self):
        for state in GeonamesCache().get_us_states():
            yield scrapy.Request(
                f"https://buenoonthego.com/mp/ndXTAL/searchByStateCode_JSON?stateCode='{state}'"
            )

    def convert_hours(self, hours):
        converted_times = ""
        if not hours:
            return ""

        if hours != "Closed":
            from_hr, to_hr = (hr.strip() for hr in hours.split("-"))
            if re.search(regex_am, from_hr):
                from_hr = re.sub(regex_am, "", from_hr)
                hour_min = from_hr.split(":")
                if len(hour_min[0]) < 2:
                    hour_min[0].zfill(2)
                converted_times += (":".join(hour_min)) + " - "
            else:
                from_hr = re.sub(regex_pm, "", from_hr)
                hour_min = from_hr.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                converted_times += (":".join(hour_min)) + " - "

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
            converted_times += "off"
        return converted_times

    def parse(self, response):
        results = response.json()
        if results:
            for i in results:
                ref = i["storeid"]
                name = i["restaurantname"]
                street = i["address1"]
                city = i["city"]
                state = i["statecode"]
                postcode = i["zipcode"]
                phone = i["phone"]
                lon = i["longitude"]
                lat = i["latitude"]
                hours = self.convert_hours(i["businesshours"])
                addr_full = "{} {}, {} {}".format(street, city, state, postcode)

                yield GeojsonPointItem(
                    ref=ref,
                    name=name,
                    street_address=street,
                    city=city,
                    state=state,
                    postcode=postcode,
                    addr_full=addr_full,
                    phone=phone,
                    lon=lon,
                    lat=lat,
                    opening_hours=hours,
                )
