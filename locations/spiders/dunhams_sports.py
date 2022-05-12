# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class DunhamsSportsSpiders(scrapy.Spider):
    name = "dunhams_sports"
    item_attributes = {"brand": "Dunham's Sports"}
    allowed_domains = ["http://www.dunhamssports.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "http://www.dunhamssports.com/wp-admin/admin-ajax.php?action=simloc_get_locations&lat=32.7258378&lng=-116.95580669999998&radius=200000",
    )

    def store_hours(self, hours):
        openHours = hours.split("-")[0].strip()
        closeHours = hours.split("-")[1].strip()

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

            return openHours + "-" + closeHours

    def parse(self, response):
        for match in response.xpath("//markers/marker"):
            fullAddress = (
                match.xpath(".//@address").extract_first().replace("<br>", ", ")
            )
            addrString = fullAddress.split(",")[0].strip()
            refString = addrString.replace(" ", "_")

            stateString = fullAddress.split(" ")[
                len(fullAddress.split(" ")) - 2
            ].strip()
            postString = fullAddress.split(" ")[len(fullAddress.split(" ")) - 1].strip()

            if len(addrString.split(" - ")) > 1:
                name = addrString.split(" - ")[0].strip()
                addrString = addrString.split(" - ")[1].strip()

            hoursMonString = self.store_hours(
                match.xpath(".//@hours_mon").extract_first().strip()
            )
            hoursSatString = self.store_hours(
                match.xpath(".//@hours_sat").extract_first().strip()
            )
            hoursSunString = self.store_hours(
                match.xpath(".//@hours_sun").extract_first().strip()
            )
            allHours = (
                "Mo-Fr "
                + hoursMonString
                + "; "
                + "Sa "
                + hoursSatString
                + "; "
                + "Su "
                + hoursSunString
            )

            yield GeojsonPointItem(
                ref=refString,
                lat=float(match.xpath(".//@lat").extract_first().strip()),
                lon=float(match.xpath(".//@lng").extract_first().strip()),
                addr_full=addrString,
                city=match.xpath(".//@city").extract_first().strip(),
                state=stateString,
                postcode=postString,
                phone=match.xpath(".//@phone").extract_first().replace(" ", ""),
                website=match.xpath(".//@permalink").extract_first().strip(),
                opening_hours=allHours,
                name=name,
            )
