import re
import scrapy

from locations.items import GeojsonPointItem


class LidlIESpider(scrapy.Spider):
    name = "lidl_ie"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["virtualearth.net"]
    start_urls = [
        "https://spatial.virtualearth.net/REST/v1/data/94c7e19092854548b3be21b155af58a1/Filialdaten-RIE/Filialdaten-RIE?&$filter=Adresstyp%20eq%201&$top=250&$format=json&$skip=0&key=AvlHnuUnvOF2tIm9bTeXIj9T4YvpuerURAEX2uC8YKY3-1Q9cWJpmxVM_tqiduGt"
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
                "city": store["CityDistrict"],
                "state": store["Locality"],
                "postcode": store["PostalCode"],
                "country": store["CountryRegion"],
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            store["AddressLine"],
                            store["CityDistrict"],
                            store["Locality"],
                            store["PostalCode"],
                            "Ireland",
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
