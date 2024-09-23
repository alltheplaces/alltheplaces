from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider

PAUL_SHARED_ATTRIBUTES = {"brand": "Paul", "brand_wikidata": "Q3370417"}


class PaulFRSpider(JSONBlobSpider):
    name = "paul_fr"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paul.fr/stores/"]

    def extract_json(self, response):
        data_raw = response.xpath('//script[contains(text(), "Smile_StoreLocator\\/retailer\\/search")]/text()').get()
        return parse_js_object(data_raw.split('markers":', 1)[1])

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["email"] = location["contact_mail"]
        item["street_address"] = item.pop("street")[0]
        yield item
