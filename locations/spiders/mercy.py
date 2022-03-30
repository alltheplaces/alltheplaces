# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class MercySpider(scrapy.Spider):
    name = "mercy"
    item_attributes = {"brand": "Mercy"}
    allowed_domains = ["mercy.net"]

    def start_requests(self):
        offsets = [*range(50, 1550, 50)]
        for offset in offsets:
            url = "https://liveapi.yext.com/v2/accounts/me/answers/vertical/query?v=20190101&api_key=b848342a24483e001b626d8df6f913db&experienceKey=mercy_health_answers&version=PRODUCTION&verticalKey=Facilities&retrieveFacets=true&limit=50&offset={offset}".format(
                offset=offset
            )
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        jsonresponse = response.json()
        locations = jsonresponse["response"]["results"]
        for location in locations:
            location_data = json.dumps(location)
            data = json.loads(location_data)

            try:
                properties = {
                    "name": data["data"]["name"],
                    "ref": data["data"]["id"],
                    "addr_full": data["data"]["address"]["line1"],
                    "city": data["data"]["address"]["city"],
                    "state": data["data"]["address"]["region"],
                    "postcode": data["data"]["address"]["postalCode"],
                    "country": data["data"]["address"]["countryCode"],
                    "website": data["data"]["c_websiteBaseURL"],
                    "lat": float(data["data"]["cityCoordinate"]["latitude"]),
                    "lon": float(data["data"]["cityCoordinate"]["longitude"]),
                }
            except:
                continue

            yield GeojsonPointItem(**properties)
