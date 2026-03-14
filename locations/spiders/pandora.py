from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest

from locations.geo import point_locations
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class PandoraSpider(RioSeoSpider):
    name = "pandora"
    item_attributes = {"brand": "Pandora", "brand_wikidata": "Q2241604"}
    end_point = "https://maps.pandora.net"
    radius = 346

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lng in point_locations("earth_centroids_iseadgg_346km_radius.csv"):
            yield JsonRequest(
                f"{self.end_point}/api/getAsyncLocations?template={self.template}&level={self.template}&radius={self.radius}&limit={self.limit}&lat={lat}&lng={lng}",
                callback=self.parse,
            )

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        if location.get("Store Type_CS") == "Authorized Retailers":
            return
        feature["phone"] = location.get("location_phone") or location.get("local_phone")
        feature["postcode"] = location.get("location_post_code") or location.get("post_code")
        feature["country"] = feature["ref"][:2].upper()
        feature["website"] = "https:" + location["indy_url"]
        feature["branch"] = feature.pop("name").removeprefix("Pandora ").removeprefix("Store ").removeprefix("@ ")
        yield feature
