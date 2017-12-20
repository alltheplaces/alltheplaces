# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

daysKey = {
    'Mon': 'Mo', 'Tue': 'Tu', 'Wed': 'We', 'Thur': 'Th',
    'Fri': 'Fr', 'Sat': 'Sa', 'Sun': 'Su'
}

class SteakNShakeSpider(scrapy.Spider):
    name = "steak_n_shake"
    allowed_domains = ["www.steaknshake.com"]
    start_urls = (
        'https://www.steaknshake.com/zsapi/locations/',
    )

    def parse_hours(self, hours):
        days = hours.split(': ')[0].strip()
        bothHours = hours.split(': ')[1].strip()

        if('-' in days):
            startDay = daysKey[days.split('-')[0].strip()]
            endDay = daysKey[days.split('-')[1].strip()]
            dayOutput = startDay + "-" + endDay
        else:
            dayOutput = daysKey[days]

        if("Closed" in bothHours):
            return ""
        if("24 hours" in bothHours):
            return dayOutput + ": 00:00-24:00; "


        openHours = bothHours.split("-")[0]
        closeHours = bothHours.split("-")[1]

        if("am" in openHours):
            openHours = openHours.replace("am","")
            if(":" in openHours):
                openH = openHours.split(":")[0]
                openM = openHours.split(":")[1]
            else:
                openH = openHours
                openM = "00"
            openHours = openH.strip() + ":" + openM.strip()

        if("pm" in openHours):
            openHours = openHours.replace("pm","")
            if(":" in openHours):
                openH = openHours.split(":")[0]
                openM = openHours.split(":")[1]
            else:
                openH = openHours
                openM = "00"
            openH = str(int(openH) + 12)
            openHours = openH.strip() + ":" + openM.strip()

        if("am" in closeHours):
            closeHours = closeHours.replace("am","")
            if(":" in closeHours):
                closeH = closeHours.split(":")[0]
                closeM = closeHours.split(":")[1]
            else:
                closeH = closeHours
                closeM = "00"
            closeHours = closeH.strip() + ":" + closeM.strip()

        if("pm" in closeHours):
            closeHours = closeHours.replace("pm","")
            if(":" in closeHours):
                closeH = closeHours.split(":")[0]
                closeM = closeHours.split(":")[1]
            else:
                closeH = closeHours
                closeM = "00"
            closeH = str(int(closeH) + 12)
            closeHours = closeH.strip() + ":" + closeM.strip()

        return dayOutput +' '+ openHours.replace(' ','') + "-" + closeHours + '; '

    def parse(self, response):
        json_string = json.loads(response.xpath("./body/p/text()").extract_first())
        for item in json_string:

            openingHoursString=""

            try:
                for s in item["hours"]["sets"][0]["hours"]:
                    if("," in item["hours"]["sets"][0]["hours"][s]):
                        for e in item["hours"]["sets"][0]["hours"][s].split(','):
                            unformattedData = s + ": " + e
                            openingHoursString = openingHoursString + self.parse_hours(unformattedData) 
                    else:
                        unformattedData = s + ": " + item["hours"]["sets"][0]["hours"][s]
                        openingHoursString = openingHoursString + self.parse_hours(unformattedData)
            except IndexError:
                openingHoursString = ""

            try:
                latFloat=item["address"]["loc"][1]
                lonFloat=item["address"]["loc"][0]
            except KeyError:
                latFloat=None
                lonFloat=None

            try:
                phoneString = item["phone1"].replace('-','')
            except KeyError:
                phoneString=None

            try:
                address2 = item["address"]["address2"]
            except KeyError:
                address2 = ""

            address = item["address"]["address1"] + " " + address2
            address = address.strip()

            yield GeojsonPointItem(
                ref=item["id"],
                name=item["name"],
                opening_hours=openingHoursString.strip(),
                addr_full=address,
                city=item["address"]["city"],
                state=item["address"]["region"],
                postcode=item["address"]["zip"],
                phone=phoneString,
                country=item["address"]["country"],
                lat=latFloat,
                lon=lonFloat,
            )

