from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaNZSpider(JSONBlobSpider):
    name = "toyota_nz"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = ["https://www.toyota.co.nz/api/dealers/all/"]

    def post_process_item(self, item, response, location):
        if location["branchType"] == 0:
            apply_category(Categories.SHOP_CAR, item)
        elif location["branchType"] == 1:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_branch_type/{location.get('branchType')}")
        if (slug := location.get("profileImageUrl")) is not None:
            item["image"] = "https://www.toyota.co.nz/" + slug
        for hours_key, tag_key in {
            "salesOpeningHours": "sales",
            "serviceOpeningHours": "service",
            "partsOpeningHours": "parts",
        }.items():
            if hours_key in location:
                item["extras"]["opening_hours:" + tag_key] = self.parse_hours(location[hours_key]).as_opening_hours()
                if item.get("opening_hours") is None:
                    item["opening_hours"] = item["extras"]["opening_hours:" + tag_key]
        yield item

    def parse_hours(self, hours_list) -> OpeningHours:
        oh = OpeningHours()
        for days_hours in hours_list:
            if "closed" in days_hours.lower():
                try:
                    for day in days_hours.lower().replace("closed", "").split("-"):
                        oh.set_closed(day.strip())
                except:
                    self.crawler.stats.inc_value(f"atp/{self.name}/hours_not_parsed/closed/{days_hours}")
            else:
                try:
                    oh.add_ranges_from_string(days_hours)
                except:
                    self.crawler.stats.inc_value(f"atp/{self.name}/hours_not_parsed/open/{days_hours}")
        return oh
