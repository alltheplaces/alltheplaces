# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import re

daysKey = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class LeesFamousRecipeSpider(scrapy.Spider):
    name = "lees_famous_recipe"
    item_attributes = {
        "brand": "Lee's Famous Recipe Chicken",
        "brand_wikidata": "Q6512810",
    }
    allowed_domains = ["www.leesfamousrecipe.com"]
    start_urls = ("https://www.leesfamousrecipe.com/locations/all",)

    def parse_phone(self, phone):
        phone = phone.replace(".", "")
        phone = phone.replace(")", "")
        phone = phone.replace("(", "")
        phone = phone.replace("_", "")
        phone = phone.replace("-", "")
        phone = phone.replace("+", "")
        phone = phone.replace(" ", "")
        return phone

    def store_hours(self, hours):
        try:
            days = hours.split(": ")[0].strip()
            if "-" in days:
                startDay = daysKey[days.split("-")[0]]
                endDay = daysKey[days.split("-")[1]]
                dayOutput = startDay + "-" + endDay
            else:
                dayOutput = daysKey[days]

            bothHours = hours.split(": ")[1].replace(" ", "")
            openHours = bothHours.split("-")[0]
            closeHours = bothHours.split("-")[1]

            if "am" in openHours:
                openHours = openHours.replace("am", "")
                if ":" in openHours:
                    openH = openHours.split(":")[0]
                    openM = openHours.split(":")[1]
                else:
                    openH = openHours
                    openM = "00"
                openHours = openH + ":" + openM

            if "pm" in openHours:
                openHours = openHours.replace("pm", "")
                if ":" in openHours:
                    openH = openHours.split(":")[0]
                    openM = openHours.split(":")[1]
                else:
                    openH = openHours
                    openM = "00"
                openH = str(int(openH) + 12)
                openHours = openH + ":" + openM

            if "am" in closeHours:
                closeHours = closeHours.replace("am", "")
                if ":" in closeHours:
                    closeH = closeHours.split(":")[0]
                    closeM = closeHours.split(":")[1]
                else:
                    closeH = closeHours
                    closeM = "00"
                closeHours = closeH + ":" + closeM

            if "pm" in closeHours:
                closeHours = closeHours.replace("pm", "")
                if ":" in closeHours:
                    closeH = closeHours.split(":")[0]
                    closeM = closeHours.split(":")[1]
                else:
                    closeH = closeHours
                    closeM = "00"
                closeH = str(int(closeH) + 12)
                closeHours = closeH + ":" + closeM
            return dayOutput + " " + openHours.replace(" ", "") + "-" + closeHours + ";"
        except (KeyError, IndexError):
            return ""

    def parse(self, response):
        if "https://www.leesfamousrecipe.com/locations/all" == response.url:
            for match in response.xpath(
                "//div[contains(@class,'field-content')]/a/@href"
            ):
                request = scrapy.Request(match.extract())
                yield request
        else:
            nameString = (
                response.xpath("//h1[@class='node-title']/text()")
                .extract_first()
                .strip()
            )
            shortString = response.xpath(
                "//h1[@class='node-title']/small/text()"
            ).extract_first()
            if shortString is None:
                shortString = ""
            nameString = nameString + " " + shortString
            nameString = nameString.strip()

            googleMapSrc = response.xpath(
                "//*[@id='block-system-main']/div/div/iframe"
            ).extract_first()
            [latString, lonString] = re.findall('center=(.*?)"', googleMapSrc)[0].split(
                ","
            )

            openingHoursString = ""
            firstHourBlock = response.xpath(
                "//div[contains(@class,'field-name-field-hours-summer')]/div/div/p/br/parent::p/text()"
            )
            for hourLine in firstHourBlock:
                openingHoursString = (
                    openingHoursString + " " + self.store_hours(hourLine.extract())
                )
            openingHoursString = openingHoursString.strip(";").strip()

            if "british-columbia" in response.url:
                countryString = "CA"
                stateString = "BC"
            else:
                countryString = "US"
                mapUrl = response.xpath(
                    "//div[contains(@class,'map-link')]/div/a/@href"
                ).extract_first()
                stateString = response.xpath(
                    "//div[contains(@class,'adr')]/div[2]/span[2]/text()"
                ).extract_first()

            yield GeojsonPointItem(
                ref=nameString,
                addr_full=response.xpath("//div[@class='street-address']/text()")
                .extract_first()
                .strip(),
                city=response.xpath(
                    "//div[@class='city-state-zip']/span[@class='locality']/text()"
                )
                .extract_first()
                .strip(),
                opening_hours=openingHoursString,
                state=stateString,
                postcode=response.xpath(
                    "//div[@class='city-state-zip']/span[@class='postal-code']/text()"
                )
                .extract_first()
                .strip(),
                phone=self.parse_phone(
                    response.xpath("//div[contains(@class,'adr')]/div[3]/text()")
                    .extract_first()
                    .strip()
                ),
                country=countryString,
                lat=float(latString),
                lon=float(lonString),
            )
