import datetime

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class RogersCommunicationsSpider(scrapy.Spider):
    name = "rogers_communications"
    item_attributes = {"brand": "Rogers Communications", "brand_wikidata": "Q165684"}
    allowed_domains = ["1-dot-rogers-store-finder.appspot.com", "rogers.com"]

    def start_requests(self):
        url = "https://1-dot-rogers-store-finder.appspot.com/searchRogersStoresService"

        headers = {
            "origin": "https://www.rogers.com",
            "Referer": "https://www.rogers.com/business/contact-us/store-locator",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        form_data = {
            "select": "Record_ID,SCID,Location_Name,Address_Or_Intersection,Address2,City,State_Or_Province,ZIP_Or_Postal_Code,Business_Phone,Intersection,Priority1,Priority2,Priority3,Priority10,Rogers_Video_Store,Rogers_Plus_Store,Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday,Closed_smb,Latitude,Longitude,CONCAT(Longitude, ',' ,Latitude) as geometry,( 6371 * acos( cos( radians(49.2827291) ) * cos( radians(Latitude) ) * cos( radians( Longitude ) - radians( -123.12073750000002) )+sin( radians(49.2827291) ) * sin( radians( Latitude )))) AS distance",
            "where": "(Closed_smb=''AND Small_biz_centre='Y')OR(Closed_smb=''AND Priority1='Y')OR(Closed_smb=''AND Priority2='Y')",
            "order": "distance ASC",
            "limit": "600",
            "channelID": "ROGERS",
        }

        yield scrapy.FormRequest(
            url=url,
            method="POST",
            formdata=form_data,
            headers=headers,
            callback=self.parse,
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for day, times in hours.items():
            if times == "CLOSED" or times == "closed" or times == "Closed":
                pass
            else:
                if "-" in times:
                    time = times.split("-")
                else:
                    time = times.split("  ")

                open_time = time[0].replace(" ", "")
                close_time = time[1].replace(" ", "")
                open_time = datetime.datetime.strptime(open_time, "%I:%M%p").strftime("%H:%M")
                close_time = datetime.datetime.strptime(close_time, "%I:%M%p").strftime("%H:%M")

                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores["features"]:
            name = store["properties"]["Address2"]
            if name == "":
                name = store["properties"]["LocationName"]

            addr = store["properties"]["AddressOrIntersection"]
            if addr[-1] == ",":
                addr = addr[:-1]

            properties = {
                "ref": store["properties"]["Record_ID"],
                "name": name,
                "street_address": addr,
                "city": store["properties"]["City"],
                "state": store["properties"]["StateOrProvince"],
                "postcode": store["properties"]["ZIPOrPostalCode"],
                "country": "CA",
                "lat": store["properties"]["Latitude"],
                "lon": store["properties"]["Longitude"],
                "phone": store["properties"]["Business_Phone"],
            }

            hours = {
                "Mo": store["properties"]["Monday"],
                "Tu": store["properties"]["Tuesday"],
                "We": store["properties"]["Wednesday"],
                "Th": store["properties"]["Thursday"],
                "Fr": store["properties"]["Friday"],
                "Sa": store["properties"]["Saturday"],
                "Su": store["properties"]["Sunday"],
            }

            try:
                h = self.parse_hours(hours)

                if h:
                    properties["opening_hours"] = h
            except:
                pass

            yield Feature(**properties)
