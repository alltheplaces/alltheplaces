from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class LornaJaneAUNZSpider(JSONBlobSpider):
    name = "lorna_jane_au_nz"
    item_attributes = {"brand": "Lorna Jane", "brand_wikidata": "Q28857986"}
    allowed_domains = ["s3.ap-southeast-2.amazonaws.com"]
    start_urls = [
        "https://s3.ap-southeast-2.amazonaws.com/cdn.folkal.com/json_response/v2/872cf56f-7317-11f0-8758-0aa8e15148ab.json",
        "https://s3.ap-southeast-2.amazonaws.com/cdn.folkal.com/json_response/v2/3e70ca1c-98d0-11f0-ae0c-0aa8e15148ab.json",
    ]
    locations_key = "locations"

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace("Lorna Jane ", "")
        item["street_address"] = merge_address_lines([item.pop("street"), item.pop("housenumber")])

        oh = OpeningHours()
        for rule in feature["timetable"]:
            if rule["isClosed"] is True:
                oh.set_closed(rule["dayOfWeek"])
            else:
                oh.add_range(rule["dayOfWeek"], rule["openTime"], rule["closeTime"])
        item["opening_hours"] = oh
        yield item
