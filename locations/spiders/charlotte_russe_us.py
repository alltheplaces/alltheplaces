from locations.json_blob_spider import JSONBlobSpider


class CharlotteRusseUSSpider(JSONBlobSpider):
    name = "charlotte_russe_us"
    item_attributes = {"brand": "Charlotte Russe", "brand_wikidata": "Q5086126"}
    allowed_domains = ["charlotterusse.com"]
    start_urls = [
        "https://charlotterusse.com/apps/api/v1/stores?location%5Blatitude%5D=40.6970193&location%5Blongitude%5D=-74.3093248&location%5Bradius%5D=2240"
    ]
    locations_key = "stores"
