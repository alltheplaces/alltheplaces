# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class WoodsCoffeeSpider(scrapy.Spider):
    name = "woods_coffee"
    item_attributes = {
        "brand": "Woods Coffee",
        "brand_wikidata": "Q8033255",
        "country": "US",
    }
    allowed_domains = ["stockist.co"]
    start_urls = ["https://stockist.co/api/v1/u11293/locations/all"]

    def store_hours(self, hours):
        hours = hours.replace("–", "-")
        hours = hours.replace("\xa0", " ")
        days = hours.split(": ")[0].strip()

        if "-" in days:
            startDay = days.split("-")[0][0:2].title()
            endDay = days.split("-")[1][0:2].title()
            dayOutput = startDay + "-" + endDay
        else:
            if "DAILY" in days:
                startDay = "Mo"
                endDay = "Su"
                dayOutput = startDay + "-" + endDay
            else:
                dayOutput = days[0:2].title()

        bothHours = hours.split(": ")[1].replace(" ", "")
        openHours = bothHours.split("-")[0]
        closeHours = bothHours.split("-")[1]

        if "AM" in openHours:
            openHours = openHours.replace("AM", "")
            if ":" in openHours:
                openH = openHours.split(":")[0]
                openM = openHours.split(":")[1]
            else:
                openH = openHours
                openM = "00"
            openHours = openH + ":" + openM

        if "PM" in openHours:
            openHours = openHours.replace("PM", "")
            if ":" in openHours:
                openH = openHours.split(":")[0]
                openM = openHours.split(":")[1]
            else:
                openH = openHours
                openM = "00"
            openH = str(int(openH) + 12)
            openHours = openH + ":" + openM

        if "AM" in closeHours:
            closeHours = closeHours.replace("AM", "")
            if ":" in closeHours:
                closeH = closeHours.split(":")[0]
                closeM = closeHours.split(":")[1]
            else:
                closeH = closeHours
                closeM = "00"
            closeHours = closeH + ":" + closeM

        if "PM" in closeHours:
            closeHours = closeHours.replace("PM", "")
            if ":" in closeHours:
                closeH = closeHours.split(":")[0]
                closeM = closeHours.split(":")[1]
            else:
                closeH = closeHours
                closeM = "00"
            closeH = str(int(closeH) + 12)
            closeHours = closeH + ":" + closeM

            return dayOutput + " " + openHours.replace(" ", "") + "-" + closeHours + ";"

    def parse(self, response):
        for store in response.json():
            hoursString = ""
            for hoursMatch in store["description"].split("\n"):
                hoursString = hoursString + " " + self.store_hours(hoursMatch)
            hoursString = hoursString.strip(";").strip()

            yield GeojsonPointItem(
                lat=store["latitude"],
                lon=store["longitude"],
                name=store["name"],
                addr_full=", ".join(
                    filter(
                        None,
                        [
                            store["address_line_1"],
                            store["address_line_2"],
                            store["city"],
                            store["state"],
                            store["postal_code"],
                            "United States",
                        ],
                    )
                ),
                city=store["city"],
                street_address=", ".join(
                    filter(None, [store["address_line_1"], store["address_line_2"]])
                ),
                state=store["state"],
                postcode=store["postal_code"],
                phone=store["phone"],
                opening_hours=hoursString,
                ref=store["id"],
            )
