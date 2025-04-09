from locations.json_blob_spider import JSONBlobSpider


class MagasinVertFRSpider(JSONBlobSpider):
    name = "magasin_vert_fr"
    allowed_domains = [
        "www.monmagasinvert.fr",
    ]
    item_attributes = {"brand": "Magasin Vert", "brand_wikidata": "Q16661975"}
    start_urls = [
        "https://www.monmagasinvert.fr/rest/mon_magasin_vert_lot1/V1/inventory/in-store-pickup/pickup-locations/?searchRequest[scopeCode]=mon_magasin_vert_lot1"
    ]
    locations_key = "items"
    needs_json_request = True

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.get("pickup_location_code")
