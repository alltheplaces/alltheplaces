from typing import Any, Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class PandoraSpider(RioSeoSpider):
    name = "pandora"
    item_attributes = {"brand": "Pandora", "brand_wikidata": "Q2241604"}
    # Not all search text give the same POIs count from this API https://maps.pandora.net/api/getAutocompleteData
    # The search text used below gives the max POIs count.
    start_urls = [
        "https://maps.pandora.net/api/getAsyncLocations?template=domain&level=domain&search=Makkah, SA&radius=10000&limit=10000",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Fix error because of some html tags
        response.json()["maplist"] = (
            response.json()["maplist"].replace('<\\/sup\\"', '</sup>\\"').replace("<sup>", "").replace("</sup>", "")
        )
        yield from RioSeoSpider.parse(self, response=response)

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        feature["phone"] = location.get("location_phone") or location.get("local_phone")
        feature["postcode"] = location.get("location_post_code") or location.get("post_code")
        feature["website"] = "https://stores.pandora.net/"
        if location.get("Store Type_CS") == "Authorized Retailers":
            feature["extras"]["secondary"] = "yes"
        yield feature
