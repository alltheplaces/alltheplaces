import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class WesternDentalUSSpider(JSONBlobSpider):
    name = "western_dental_us"
    item_attributes = {
        "brand": "Western Dental",
        "brand_wikidata": "Q64211989",
    }
    start_urls = ["https://www.westerndental.com/en-us/find-a-location"]

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var locationsInit = ")]/text()').get()
        )

    def post_process_item(self, item, response, location):
        item["branch"] = location["StoreNickname"].title()
        item["street_address"] = item.pop("addr_full")
        item["website"] = response.urljoin(location["DocumentUrlPath"])
        item["postcode"] = str(item["postcode"])
        apply_category(Categories.DENTIST, item)
        yield item
