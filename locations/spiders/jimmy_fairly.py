import json

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class JimmyFairlySpider(JSONBlobSpider):
    name = "jimmy_fairly"
    item_attributes = {
        "brand": "Jimmy Fairly",
        "brand_wikidata": "Q104825419",
    }
    start_urls = ["https://www.jimmyfairly.com/pages/stores"]

    def extract_json(self, response):
        data = response.xpath('//script[contains(@x-ref,"json")]/text()').get()

        if not data:
            raise ValueError("data not found")

        data = json.loads(data)
        extract = []
        for f in data["features"]:
            extract.append(f["properties"])

        return extract

    @staticmethod
    def format_hour(value):
        if not value.isdigit() or len(value) != 4:
            return None

        hour = int(value[:2])
        minute = int(value[2:])

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        return f"{hour:02d}:{minute:02d}"

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_OPTICIAN, item)
        if location.get("url") is not None:
            item["website"] = "https://www.jimmyfairly.com" + location["url"]

        item["branch"] = item.pop("name", "").removeprefix("Jimmy Fairly - ")

        if location.get("opening_hours") is not None:
            item["opening_hours"] = OpeningHours()
            invalid = False

            for day, time in location["opening_hours"].items():
                day = day[:2].capitalize()
                if day not in DAYS:
                    continue

                if not isinstance(time, str):
                    invalid = True
                elif time == "" or time.lower() == "closed":
                    item["opening_hours"].set_closed(day)
                elif not invalid:
                    midday_break = time.split("|")

                    if len(midday_break) > 2:  # the syntax is invalid, skipping the opening hours for this shop
                        invalid = True
                        break

                    for time in midday_break:
                        hours = time.split("-")
                        if len(hours) == 2:
                            openinghour = self.format_hour(hours[0])
                            closinghour = self.format_hour(hours[1])
                            if (
                                openinghour is None or closinghour is None
                            ):  # the syntax is invalid, skipping the opening hours for this shop
                                invalid = True
                                break

                            item["opening_hours"].add_range(day, openinghour, closinghour)
                        else:  # the syntax is invalid, skipping the opening hours for this shop
                            invalid = True
                            break

                if invalid:
                    item["opening_hours"] = None
                    break

        yield item
