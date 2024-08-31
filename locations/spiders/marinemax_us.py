from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class MarinemaxUSSpider(AlgoliaSpider):
    name = "marinemax_us"
    item_attributes = {"brand": "MarineMax", "brand_wikidata": "Q119140995"}
    app_id = "MES124X9KA"
    api_key = "2a57d01f2b35f0f1c60cb188c65cab0d"
    index_name = "StoreLocations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["isActive"]:
            return
        item["ref"] = feature["IDS_Site_ID"]
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["street_address"] = clean_address([feature["Address1"], feature["Address2"]])
        item["state"] = feature["State"]
        item["email"] = feature["OwnerEmailAddress"]
        item["website"] = feature["LocationPageURL"]
        yield item
