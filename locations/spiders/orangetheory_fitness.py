import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.items import Feature


class OrangetheoryFitnessSpider(scrapy.Spider):
    name = "orangetheory_fitness"
    item_attributes = {"brand": "Orangetheory Fitness", "brand_wikidata": "Q25005163"}
    allowed_domains = ["orangetheory.co"]
    start_urls = [
        "https://api.orangetheory.co/partners/studios/v2?country=United+States",
        "https://api.orangetheory.co/partners/studios/v2?country=Canada",
        "https://api.orangetheory.co/partners/studios/v2?country=Australia",
        "https://api.orangetheory.co/partners/studios/v2?country=Chile",
        "https://api.orangetheory.co/partners/studios/v2?country=China",
        "https://api.orangetheory.co/partners/studios/v2?country=Colombia",
        "https://api.orangetheory.co/partners/studios/v2?country=Costa+Rica",
        "https://api.orangetheory.co/partners/studios/v2?country=Dominican+Republic",
        "https://api.orangetheory.co/partners/studios/v2?country=Germany",
        "https://api.orangetheory.co/partners/studios/v2?country=Guatemala",
        "https://api.orangetheory.co/partners/studios/v2?country=Hong+Kong",
        "https://api.orangetheory.co/partners/studios/v2?country=India",
        "https://api.orangetheory.co/partners/studios/v2?country=Israel",
        "https://api.orangetheory.co/partners/studios/v2?country=Japan",
        "https://api.orangetheory.co/partners/studios/v2?country=Kuwait",
        "https://api.orangetheory.co/partners/studios/v2?country=Mexico",
        "https://api.orangetheory.co/partners/studios/v2?country=New+Zealand",
        "https://api.orangetheory.co/partners/studios/v2?country=Peru",
        "https://api.orangetheory.co/partners/studios/v2?country=Puerto+Rico",
        "https://api.orangetheory.co/partners/studios/v2?country=Singapore",
        "https://api.orangetheory.co/partners/studios/v2?country=Spain",
        "https://api.orangetheory.co/partners/studios/v2?country=United+Arab+Emirates",
        "https://api.orangetheory.co/partners/studios/v2?country=United+Kingdom",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_data = json.loads(response.text)
        locations = location_data["data"]

        for location in locations:
            # Handle junk data
            if " live" in location[0]["studioName"].lower():  # Skip Orangetheory Live virtual records
                continue
            if location[0]["studioLocation"]["physicalAddress"] in [
                "*",
                "a",
            ]:  # Skip placeholder records
                continue
            if location[0]["studioLocation"]["longitude"] in [
                "1.00000000",
                "0.00000000",
            ]:  # Skip test records
                continue
            if location[0]["studioName"] == "LatLong":  # Skip latlon placeholder record
                continue

            # Handle coordinates
            if float(location[0]["studioLocation"]["latitude"]) < -55.0:  # Drop handful of bad coords in Antarctica
                lat = lon = ""
            elif float(location[0]["studioLocation"]["longitude"]) < -180.0:  # Drop handful of bad coords
                lat = lon = ""
            else:
                lat = location[0]["studioLocation"]["latitude"]
                lon = location[0]["studioLocation"]["longitude"]

            properties = {
                "ref": location[0]["studioId"],
                "name": location[0]["studioName"],
                "street_address": location[0]["studioLocation"]["physicalAddress"].strip(),
                "city": location[0]["studioLocation"]["physicalCity"],
                "state": location[0]["studioLocation"]["physicalState"],
                "postcode": location[0]["studioLocation"]["physicalPostalCode"],
                "country": location[0]["studioLocation"]["physicalCountry"],
                "lat": lat,
                "lon": lon,
                "phone": location[0]["studioLocation"]["phoneNumber"],
            }

            yield Feature(**properties)
