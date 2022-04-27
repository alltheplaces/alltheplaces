# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem


class LidlGBSpider(scrapy.Spider):
    name = "lidl_gb"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["virtualearth.net"]
    start_urls = [
        "https://spatial.virtualearth.net/REST/v1/data/588775718a4b4312842f6dffb4428cff/Filialdaten-UK/Filialdaten-UK?$filter=Adresstyp%20Eq%201&$top=250&$format=json&$skip=0&key=Argt0lKZTug_IDWKC5e8MWmasZYNJPRs0btLw62Vnwd7VLxhOxFLW2GfwAhMK5Xg",
    ]
    download_delay = 1

    def parse(self, response):
        data = response.json()
        stores = data["d"]["results"]

        for store in stores:
            properties = {
                "name": store["ShownStoreName"],
                "ref": store["EntityID"],
                "street_address": store["AddressLine"],
                "city": store["PostalCode"],
                "postcode": store["Locality"],
                "country": store["CountryRegion"],
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["AddressLine"],
                            store["CityDistrict"],
                            store["PostalCode"],
                            store["Locality"],
                            "United Kingdom",
                        ),
                    )
                ),
                "lat": float(store["Latitude"]),
                "lon": float(store["Longitude"]),
                "extras": {},
            }

            if store["INFOICON17"] == "customerToilet":
                properties["extras"]["toilets"] = "yes"
                properties["extras"]["toilets:access"] = "customers"

            yield GeojsonPointItem(**properties)

        if stores:
            i = int(re.search(r"\$skip=(\d+)&", response.url).groups()[0])
            url_parts = response.url.split("$skip={}".format(i))
            i += 250
            url = "$skip={}".format(i).join(url_parts)
            yield scrapy.Request(url=url)
