from locations.json_blob_spider import JSONBlobSpider


class KuoniGBSpider(JSONBlobSpider):
    name = "kuoni_gb"
    item_attributes = {"brand": "Kuoni", "brand_wikidata": "Q684355"}
    start_urls = ["https://www.kuoni.co.uk/api/appointment/get-stores/?r=20250609123615"]
