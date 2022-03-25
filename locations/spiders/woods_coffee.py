# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem

daysKey = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class WoodsCoffeeSpider(scrapy.Spider):
    name = "woods_coffee"
    item_attributes = {"brand": "Woods Coffee", "brand_wikidata": "Q8033255"}
    allowed_domains = ["www.woodscoffee.com"]
    start_urls = ("https://woodscoffee.com/locations/",)

    def store_hours(self, hours):
        hours = hours.replace("–", "-")
        hours = hours.replace("\xa0", " ")
        days = hours.split(": ")[0].strip()

        if "-" in days:
            startDay = daysKey[days.split("-")[0]]
            endDay = daysKey[days.split("-")[1]]
            dayOutput = startDay + "-" + endDay
        else:
            if "DAILY" in days:
                startDay = "Mo"
                endDay = "Su"
                dayOutput = startDay + "-" + endDay
            else:
                dayOutput = daysKey[days]

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
        for match in response.xpath(
            "//h2[contains(@class,'font-weight-700 text-uppercase')]/parent::div/parent::div/parent::div"
        ):
            cityState = match.xpath(
                ".//div[contains(@class,'heading-text el-text')]/div/p/text()"
            ).extract_first()
            cityString = cityState.split(",")[0].strip()
            stateString = cityState.split(",")[1].strip()

            addressString = (
                match.xpath(
                    ".//div[contains(@class,'uncode_text_column')]/p[contains(@style,'text-align: center;')][not(.//strong)]/text()"
                )
                .extract_first()
                .strip()
            )
            postcodeString = addressString.split(stateString)[1].strip()
            addressString = (
                addressString.split(stateString)[0]
                .replace(",", "")
                .strip()
                .strip(cityString)
                .strip()
            )

            if (
                match.xpath(
                    ".//div[contains(@class,'uncode_text_column')]/p[contains(@style,'text-align: center;')][not (.//strong)]/br/following-sibling::text()"
                ).extract_first()
                is None
            ):
                phoneString = ""
            else:
                phoneString = match.xpath(
                    ".//div[contains(@class,'uncode_text_column')]/p[contains(@style,'text-align: center;')][not (.//strong)]/br/following-sibling::text()"
                ).extract_first()
            phoneString = phoneString.replace(" ", "").strip()

            hoursString = ""
            for hoursMatch in match.xpath(
                ".//p[contains(@style,'text-align: center;')]/strong//following-sibling::text()"
            ):
                hoursString = (
                    hoursString
                    + " "
                    + self.store_hours(hoursMatch.extract().replace("\n", ""))
                )
            hoursString = hoursString.strip(";").strip()

            name = match.xpath(
                ".//h2[contains(@class,'font-weight-700 text-uppercase')]/span/text()"
            ).extract_first()

            yield GeojsonPointItem(
                ref=name,
                name=name,
                addr_full=addressString,
                city=cityString,
                state=stateString,
                postcode=postcodeString,
                country="USA",
                phone=phoneString,
                opening_hours=hoursString,
                website=response.urljoin(match.xpath(".//a/@href").extract_first()),
            )
