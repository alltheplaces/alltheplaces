import chompjs
from locations.json_blob_spider import JSONBlobSpider


class LegitZASpider(JSONBlobSpider):
    name = "legit_za"
    start_urls = ["https://amaicdn.com/storelocator-prod/wtb/legit-za-1724151185.js"]

    def extract_json(self, response):
        chunks = response.text.split("SCASLWtb=")
        return chompjs.parse_js_object(chunks[1])['locations']

