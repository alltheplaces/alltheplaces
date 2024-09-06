import chompjs

from locations.json_blob_spider import JSONBlobSpider


class DunnsSpider(JSONBlobSpider):
    name = "dunns"
    start_urls = ["https://amaicdn.com/storelocator-prod/wtb/dunnssa-1724934424.js"]
    item_attributes = {"brand": "Dunns", "brand_wikidata": "Q116619823"}

    def extract_json(self, response):
        chunks = response.text.split("SCASLWtb=")
        return chompjs.parse_js_object(chunks[1])["locations"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
