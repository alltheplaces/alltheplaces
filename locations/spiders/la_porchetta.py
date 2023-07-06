from locations.storefinders.storepoint import StorepointSpider


class LaPorchettaSpider(StorepointSpider):
    name = "la_porchetta"
    item_attributes = {"brand": "La Porchetta", "brand_wikidata": "Q6464528"}
    key = "16156af5878536"
