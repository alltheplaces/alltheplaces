import json
from collections import defaultdict

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class MountainAmericaCreditUnionUSSpider(JSONBlobSpider):
    name = "mountain_america_credit_union_us"
    item_attributes = {
        "brand": "Mountain America Credit Union",
        "brand_wikidata": "Q6924862",
        "extras": Categories.BANK.value,
    }
    start_urls = ["https://www.macu.com/page-data/branch-locations/page-data.json"]
    locations_key = ["result", "pageContext", "frontmatter", "tableEntries", "branches"]

    def post_process_item(self, item, response, location):
        if location["id"] == "member_service_team":
            return

        del item["name"]
        item["ref"] = location["branch_id"]
        item["state"], _ = location["name"].split(" - ")
        item["branch"] = location["headline"]
        item["street_address"] = location["address_line_1"]
        item["addr_full"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
        item["phone"] = location["phone"]
        item["website"] = response.urljoin(location["details_url"])

        open_close_times = json.loads(location["open_close_times"])
        opening_hours = defaultdict(OpeningHours)
        for day, open_types in open_close_times.items():
            for open_type, open_close in open_types.items():
                opening_hours[open_type].add_range(
                    day, open_close["open"], open_close["closed"], time_format="%H:%M:%S"
                )
        item["opening_hours"] = opening_hours["lobby"]
        item["extras"]["opening_hours:drive_through"] = opening_hours["driveUp"].as_opening_hours()

        yield item
