from locations.json_blob_spider import JSONBlobSpider


class ProHockeyLifeCASpider(JSONBlobSpider):
    name = "pro_hockey_life_ca"
    item_attributes = {"brand": "Pro Hockey Life", "brand_wikidata": "Q123466336"}
    start_urls = ["https://www.prohockeylife.com/cdn/shop/t/37/assets/stores.json"]
    locations_key = "data"
