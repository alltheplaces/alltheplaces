from locations.storefinders.storepoint import StorepointSpider


class FatBastardBurritoCASpider(StorepointSpider):
    name = "fat_bastard_burrito_ca"
    item_attributes = {
        "brand_wikidata": "Q123865546",
        "brand": "Fat Bastard Burrito",
    }
    key = "165e89d43b14a9"
