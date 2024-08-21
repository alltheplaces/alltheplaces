from chompjs import parse_js_object

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class WillscotCAUSSpider(JSONBlobSpider):
    name = "willscot_ca_us"
    item_attributes = {"brand": "WillScot", "brand_wikidata": "Q123415387", "extras": Categories.SHOP_RENTAL.value}
    allowed_domains = ["www.willscot.com"]
    start_urls = ["https://www.willscot.com/en/locations"]

    def extract_json(self, response):
        branches_raw = (
            response.xpath("//script[contains(text(), ',\\\"branches\\\":')]/text()")
            .get()
            .replace('\\"', '"')
            .replace("\\\\n", " ")
            .replace("\\", " ")
        )
        branches_raw = branches_raw.split(',"branches":', 1)[1]
        features_dict = parse_js_object(branches_raw)
        return features_dict

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name", None)
        item["website"] = "https://www.willscot.com/en/locations/{}/{}".format(location["stateSlug"], location["slug"])
        if location.get("openingHours"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["openingHours"])
        yield item
