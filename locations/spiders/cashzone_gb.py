import hashlib
from typing import AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest

from locations.geo import point_locations
from locations.items import Feature


class CashzoneGBSpider(Spider):
    name = "cashzone_gb"
    item_attributes = {"brand": "Cashzone", "brand_wikidata": "Q110738461"}

    async def start(self) -> AsyncIterator[FormRequest]:
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "UK"):
            yield FormRequest(
                url="https://bankmachine.locatorsearch.com/GetItems.aspx",
                formdata={
                    "lat": str(lat),
                    "lng": str(lon),
                    "searchby": "ATMSF",
                },
            )

    def parse(self, response, **kwargs):
        response = Selector(text=response.text, type="xml")
        for marker in response.xpath("//markers/marker"):
            item = Feature()
            item["lat"] = marker.xpath("./@lat").get()
            item["lon"] = marker.xpath("./@lng").get()
            item["name"] = marker.xpath("./label/text()").get().replace("<br>", ", ")
            item["street_address"] = marker.xpath("./tab/add1/text()").get()
            item["addr_full"] = ", ".join(
                [
                    item["street_address"],
                    marker.xpath("./tab/add2/text()").get(),
                ]
            )
            item["ref"] = hashlib.sha256(
                (item["name"] + item["addr_full"] + item["lat"] + item["lon"]).encode("utf_8")
            ).hexdigest()

            yield item
