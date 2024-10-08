import urllib
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class PhotomeGBSpider(Spider):
    name = "photome_gb"
    item_attributes = {"brand": "Photo-Me", "brand_wikidata": "Q123456627"}
    base_url = (
        "https://services5.arcgis.com/M6ZM30o7d7nGnSp2/arcgis/rest/services/Photo_Me_map_220223/FeatureServer/0/query?"
    )
    fields = ["Lookup", "machine_code", "place_name", "postal_code", "family_reference", "Machine_type", "FID"]

    def get_request(self, offset: int, size: int = 1000) -> Request:
        return JsonRequest(
            url=self.base_url
            + urllib.parse.urlencode(
                {
                    "where": "1=1",
                    "inSR": "4326",
                    "outFields": ",".join(self.fields),
                    "resultOffset": str(offset),
                    "resultRecordCount": str(size),
                    "f": "geojson",
                }
            ),
            meta={"offset": offset, "size": size},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.get_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            item = Feature()
            item["geometry"] = location["geometry"]
            item["ref"] = location["id"]

            yield from self.parse_item(item, location, location["properties"]) or []

        if response.json().get("properties", {}).get("exceededTransferLimit"):
            yield self.get_request(response.meta["offset"] + response.meta["size"], response.meta["size"])

    def parse_item(self, item: Feature, location: dict, properties: dict) -> Iterable[Feature]:
        item["branch"] = properties["place_name"]
        item["postcode"] = properties["postal_code"]
        yield item
