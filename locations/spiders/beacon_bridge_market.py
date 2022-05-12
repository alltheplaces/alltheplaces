# -*- coding: utf-8 -*-
import scrapy
import traceback

from locations.items import GeojsonPointItem

URL = "http://www.beaconandbridge.com/wp-admin/admin-ajax.php"
HEADERS = {
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.6",
    "Origin": "http://www.beaconandbridge.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "application/json, text/plain, */*",
    "Referer": "http://www.beaconandbridge.com/locations/",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}


class BeaconAndBridgeSpider(scrapy.Spider):
    name = "beacon_and_bridge"
    item_attributes = {"brand": "Beacon Bridge Market"}
    allowed_domains = ["www.beaconandbridge.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        form_data = {
            "formdata": "addressInput=",
            "lat": "43.0142978",
            "lng": "-83.68935469999997",
            "radius": "10000",
            "action": "csl_ajax_onload",
        }

        yield scrapy.http.FormRequest(
            url=URL,
            method="POST",
            formdata=form_data,
            headers=HEADERS,
            callback=self.parse,
        )

    def parse(self, response):
        results = response.json()
        for data in results["response"]:
            properties = {
                "ref": data["id"],
                "name": data["name"],
                "lat": data["lat"],
                "lon": data["lng"],
                "addr_full": data["address"],
                "city": data["city"],
                "state": data["state"],
                "postcode": data["zip"],
                "country": data["country"],
                "phone": data["phone"],
                "website": data["url"],
            }

            yield GeojsonPointItem(**properties)
