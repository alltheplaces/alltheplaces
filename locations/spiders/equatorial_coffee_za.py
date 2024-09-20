import chompjs

from locations.json_blob_spider import JSONBlobSpider


class EquatorialCoffeeZASpider(JSONBlobSpider):
    name = "equatorial_coffee_za"
    item_attributes = {
        "brand_wikidata": "Q130074908",
        "brand": "Equatorial Coffee",
    }
    start_urls = ["https://equatorialcoffee.net/coffee-near-me"]
    no_refs = True

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('.//script[contains(text(), "var stores = [")]').get())

    def pre_process_data(self, feature, **kwargs):
        if feature["Country"] == "SA":
            feature["Country"] = "ZA"

    def post_process_item(self, item, response, location):
        item["branch"] = location["Site Name"]
        yield item
