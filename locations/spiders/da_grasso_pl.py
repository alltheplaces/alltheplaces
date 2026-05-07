from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class DaGrassoPLSpider(JSONBlobSpider):
    name = "da_grasso_pl"
    item_attributes = {"brand": "Da Grasso", "brand_wikidata": "Q11692586"}
    start_urls = ["https://api.dagrasso.pl/localization-api/api/v2/stores/pickup"]

    def post_process_item(self, item, response, feature):
        if raw_name := item.pop("name", ""):
            item["branch"] = raw_name.replace("aaa.", "").strip()

        self.parse_opening_hours(item, feature)
        yield item

    def parse_opening_hours(self, item, feature):
        opening_times = feature.get("openingTimes", [])
        closing_times = feature.get("closingTimes", [])

        if opening_times and closing_times:
            oh = OpeningHours()
            oh.add_days_range(DAYS, opening_times[0].split("T")[1][:5], closing_times[0].split("T")[1][:5])
            item["opening_hours"] = oh
