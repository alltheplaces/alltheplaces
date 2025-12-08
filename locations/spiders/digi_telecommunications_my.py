from locations.storefinders.storepoint import StorepointSpider


class DigiTelecommunicationsMYSpider(StorepointSpider):
    name = "digi_telecommunications_my"
    item_attributes = {"brand": "Digi", "brand_wikidata": "Q3268530"}
    key = "1624a4f7eafca0"
