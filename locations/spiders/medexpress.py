import re

import scrapy

from locations.items import Feature


class MedexpressSpider(scrapy.Spider):
    name = "medexpress"
    item_attributes = {"brand": "MedExpress", "brand_wikidata": "Q102183820"}
    allowed_domains = ["medexpress.com"]
    start_urls = ("https://www.medexpress.com/bin/optum3/medexserviceCallToYEXT2",)

    def parse(self, response):
        data = response.json()
        stores = data["locations"]

        for store in stores:
            if re.search("closed", store["locationName"], re.IGNORECASE):
                continue

            properties = {
                "ref": store["uid"],
                "name": store["locationName"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "lat": store["yextDisplayLat"],
                "lon": store["yextDisplayLng"],
                "phone": store["phone"],
            }

            if "Coming soon" not in store["address"]:
                properties["street_address"] = store["address"]

            if "displayWebsiteUrl" in store:
                properties["website"] = store["displayWebsiteUrl"]

            # All of the Medexpress locations' hours are Mo-Su 08:00-20:00.
            if (
                "hours" in store
                and store["hours"]
                and store["hours"]
                == "1:8:00:20:00,2:8:00:20:00,3:8:00:20:00,4:8:00:20:00,5:8:00:20:00,6:8:00:20:00,7:8:00:20:00"
            ):
                properties["opening_hours"] = "Mo-Su 08:00-20:00"

            yield Feature(**properties)
