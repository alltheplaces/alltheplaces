from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class OcharleysUSSpider(JSONBlobSpider):
    name = "ocharleys_us"
    item_attributes = {"brand": "O'Charley's", "brand_wikidata": "Q7071703"}
    start_urls = ["https://api.storyblok.com/v2/cdn/stories?per_page=100&token=QDWF1ALGFGpoSSyr9dCtQAtt"]

    def extract_json(self, response):
        return DictParser.get_nested_key(response.json(), "locations")

    def post_process_item(self, item, response, feature):
        item.pop("name")
        item["website"] = f"https://www.ocharleys.com/locations/{feature['path']}"
        item["street_address"] = item.pop("addr_full")

        oh = OpeningHours()
        for line in feature["hours"]:
            oh.add_range(line["day"], line["open"], line["close"])
        item["opening_hours"] = oh

        yield item
