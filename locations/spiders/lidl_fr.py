import scrapy

from locations.items import GeojsonPointItem
from locations.spiders.lidl_gb import LidlGBSpider


class LidlFRSpider(scrapy.Spider):
    name = "lidl_fr"
    item_attributes = LidlGBSpider.item_attributes
    allowed_domains = ["virtualearth.net"]
    base_url = (
        "https://spatial.virtualearth.net/REST/v1/data/717c7792c09a4aa4a53bb789c6bb94ee/Filialdaten-FR/Filialdaten-FR"
        "?key=AgC167Ojch2BCIEvqkvyrhl-yLiZLv6nCK_p0K1wyilYx4lcOnTjm6ud60JnqQAa"
        "&$filter=Adresstyp Eq 1"
        "&$select=EntityID,ShownStoreName,AddressLine,Locality,PostalCode,CountryRegion,CityDistrict,Latitude,Longitude"
    )

    def start_requests(self):
        yield scrapy.Request(
            self.base_url + "&$inlinecount=allpages" + "&$format=json",
            callback=self.get_pages,
        )

    def get_pages(self, response):
        total_count = int(response.json()["d"]["__count"])
        offset = 0
        page_size = 250

        while offset < total_count:
            yield scrapy.Request(self.base_url + f"&$top={page_size}&$skip={offset}&$format=json")
            offset += page_size

    def parse(self, response):
        stores = response.json()["d"]["results"]

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
