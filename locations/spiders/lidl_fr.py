# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem


class LidlFRSpider(scrapy.Spider):
    name = "lidl_fr"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["virtualearth.net"]
    start_urls = [
        "https://spatial.virtualearth.net/REST/v1/data/717c7792c09a4aa4a53bb789c6bb94ee/Filialdaten-FR/Filialdaten-FR?$filter=Adresstyp%20Eq%201&$top=250&$format=json&$skip=0&key=AgC167Ojch2BCIEvqkvyrhl-yLiZLv6nCK_p0K1wyilYx4lcOnTjm6ud60JnqQAa"
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
                "city": store["Locality"],
                "postcode": store["PostalCode"],
                "country": store["CountryRegion"],
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["AddressLine"],
                            store["Locality"],
                            store["CityDistrict"],
                            store["PostalCode"],
                            "France",
                        ),
                    )
                ),
                "lat": float(store["Latitude"]),
                "lon": float(store["Longitude"]),
            }

            yield GeojsonPointItem(**properties)

        if stores:
            i = int(re.search(r"\$skip=(\d+)&", response.url).groups()[0])
            url_parts = response.url.split("$skip={}".format(i))
            i += 250
            url = "$skip={}".format(i).join(url_parts)
            yield scrapy.Request(url=url)
