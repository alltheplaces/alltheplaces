from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


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
        oh = OpeningHours()
        for day_time in feature.get("timetable"):
            day = day_time.get("dayOfWeek")
            open_time = day_time.get("openTime")
            close_time = day_time.get("closeTime")
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
