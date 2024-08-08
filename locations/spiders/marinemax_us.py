from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.algolia import AlgoliaSpider


class MarinemaxUSSpider(AlgoliaSpider):
    name = "marinemax_us"
    item_attributes = {"brand": "MarineMax", "brand_wikidata": "Q119140995"}
    app_id = "MES124X9KA"
    api_key = "2a57d01f2b35f0f1c60cb188c65cab0d"
    index_name = "StoreLocations"

    def parse_item(self, item, location):
        if not location["isActive"]:
            return
        item["ref"] = location["IDS_Site_ID"]
        item["lat"] = location["_geoloc"]["lat"]
        item["lon"] = location["_geoloc"]["lng"]
        item["street_address"] = clean_address([location["Address1"], location["Address2"]])
        item["state"] = location["State"]
        item["email"] = location["OwnerEmailAddress"]
        item["website"] = location["LocationPageURL"]
        yield item
