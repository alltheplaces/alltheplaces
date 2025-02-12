import re

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


# A variant on the SuperStoreFinder plugin
class KingPieZASpider(JSONBlobSpider):
    name = "king_pie_za"
    item_attributes = {"brand": "King Pie", "brand_wikidata": "Q116619039"}
    start_urls = ["https://www.kingpie.co.za/wp-content/uploads/ssf-wp-uploads/ssf-data.json"]
    locations_key = "item"

    def post_process_item(self, item, response, location):
        if item["website"] == "https://www.kingpie.co.za/":
            item.pop("website")

        item["opening_hours"] = oh = OpeningHours()
        oh.add_ranges_from_string(
            re.sub(r"<[^>]*>|&nbsp;", " ", location["operatingHours"]).replace("24hrs", "00:00 - 23:59")
        )
        yield item
