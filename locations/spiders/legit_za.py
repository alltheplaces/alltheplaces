import chompjs

from locations.json_blob_spider import JSONBlobSpider


class LegitZASpider(JSONBlobSpider):
    name = "legit_za"
    start_urls = ["https://amaicdn.com/storelocator-prod/wtb/legit-za-1724151185.js"]
    item_attributes = {"brand": "LEGiT", "brand_wikidata": "Q122959274"}

    def extract_json(self, response):
        chunks = response.text.split("SCASLWtb=")
        return chompjs.parse_js_object(chunks[1])["locations"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        yield item
