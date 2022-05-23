# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SwissChaletSpider(scrapy.Spider):
    name = "swiss_chalet"
    item_attributes = {"brand": "Swiss Chalet", "brand_wikidata": "Q2372909"}
    allowed_domains = ["swisschalet.com"]
    start_urls = [
        "https://iosapi.swisschalet.com/CaraAPI/servlet/VESBCmdServlet?application=VECOMV1&service=AuthenticationService&command=createSession&reqJSON=%7B%22request%22%3A%7B%22requestHeader%22%3A%7B%22caller%22%3A%22Mobile%22%7D%2C%22requestContent%22%3A%7B%22@class%22%3A%22createSessionRqstModel%22%2C%22lang%22%3A%22en%22%2C%22version%22%3A%221.0.1%22%2C%22appType%22%3A%22web%22%7D%7D%7D",
    ]

    def parse(self, response):
        base_url = "https://iosapi.swisschalet.com/CaraAPI/servlet/VESBCmdServlet?application=VECOMV1&service=OrganizationService&command=getStoreList&reqJSON=%7B%22request%22%3A%7B%22requestHeader%22%3A%7B%22caller%22%3A%22Mobile%22%2C%22sessionId%22%3A%22{session_id}%22%7D%2C%22requestContent%22%3A%7B%22@class%22%3A%22storeListRqstModel%22%2C%22eCommOnly%22%3A%22N%22%2C%22fromLatitude%22%3A90.0000%2C%22toLatitude%22%3A0.00000%2C%22fromLongitude%22%3A-180.0000%2C%22toLongitude%22%3A-1.56301%7D%7D%7D"
        info = response.json()
        session_id = info["response"]["responseContent"]["veSessionID"]

        url = base_url.format(session_id=session_id)
        yield scrapy.Request(url=url, callback=self.parse_places)

    def parse_places(self, response):
        places = response.json()

        for place in places["response"]["responseContent"]["storeModel"]:
            properties = {
                "ref": place["storeNumber"],
                "name": place["storeName"],
                "addr_full": str(place["streetNumber"]) + " " + place["street"],
                "city": place["city"],
                "state": place["province"],
                "postcode": place["postalCode"],
                "country": "CA",
                "lat": place["latitude"],
                "lon": place["longitude"],
                "phone": place["phoneNumber"],
            }

            yield GeojsonPointItem(**properties)
