from locations.storefinders.location_bank import LocationBankSpider


class TopCarpetsAndFloorsZASpider(LocationBankSpider):
    name = "top_carpets_and_floors_za"
    client_id = "f3e8ee52-c55d-449b-b35a-d7def6ea5e51"
    item_attributes = {
        "brand": "Top Carpets & Floors",
        "brand_wikidata": "Q120765450",
    }
