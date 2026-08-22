import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.hours import DAYS, OpeningHours

import json


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


    def post_process_item(self, item, response, location):
        if location.get("url") is not None:
            item["website"] = "https://www.jimmyfairly.com" + location["url"]

        item["branch"] = item.pop("name", "").removeprefix("Jimmy Fairly - ")

        if location.get("opening_hours") is not None:
            item["opening_hours"] = OpeningHours()
            for day,time in location["opening_hours"].items():
                day = day[:2].capitalize()
                if(day not in DAYS):
                    continue
        
                if(time == ""):
                    item["opening_hours"].set_closed(day)
                else:
                    midday_break = time.split("|")
                    for time in midday_break:
                        hours = time.split("-")
                        if(len(hours) == 2):
                            openinghour = hours[0][:2] + ":" + hours[0][2:]
                            closinghour = hours[1][:2] + ":" + hours[1][2:]
                            item["opening_hours"].add_range(day,openinghour,closinghour)

        yield item
