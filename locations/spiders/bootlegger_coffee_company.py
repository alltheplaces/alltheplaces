import chompjs

from locations.json_blob_spider import JSONBlobSpider


class BootleggerCoffeeCompanySpider(JSONBlobSpider):
    name = "bootlegger_coffee_company"
    item_attributes = {"brand": "Bootlegger Coffee Company", "brand_wikidata": "Q116646503"}
    start_urls = [
        "https://shy.elfsight.com/p/boot/?callback=__esappsPlatformBoot4146878327&shop=bootlegger-coffee.myshopify.com&w=8212fde6-c29c-44b5-bc63-5ebddf7f3b40"
    ]
    no_refs = True  # not all locations seem to have an id

    def extract_json(self, response):
        data = chompjs.parse_js_object(response.text)
        return data["data"]["widgets"]["8212fde6-c29c-44b5-bc63-5ebddf7f3b40"]["data"]["settings"]["markers"]

    def pre_process_data(self, location):
        location["addr"] = location.pop("infoAddress")
        location["phone"] = location.pop("infoPhone")
        location["email"] = location.pop("infoEmail")
        location["lat"], location["lon"] = location.get("coordinates").split(", ", 1)

    def post_process_item(self, item, response, location):
        item["branch"] = location.pop("infoTitle")
        if "COMING SOON" not in item["branch"]:
            yield item
