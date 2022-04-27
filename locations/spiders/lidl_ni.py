import re
import scrapy

from locations.items import GeojsonPointItem


class LidlNISpider(scrapy.Spider):
    name = "lidl_ni"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["virtualearth.net"]
    start_urls = [
        "https://spatial.virtualearth.net/REST/v1/data/91bdba818b3c4f5e8b109f223ac4a9f0/Filialdaten-NIE/Filialdaten-NIE?&$filter=Adresstyp%20eq%201&$top=250&$format=json&$skip=0&key=Asz4OJrOqSHy-1xEWYGLbFhH4TnVP0LL1xgj0YBkewA5ZrtHRB2nlpfqzm1lqKPK"
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
                            store["PostalCode"],
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
