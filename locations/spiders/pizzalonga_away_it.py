import re

import chompjs

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


def add_it_ranges(oh, string):
    oh.add_ranges_from_string(
        string,
        days=DAYS_IT,
        named_day_ranges=NAMED_DAY_RANGES_IT,
        named_times=NAMED_TIMES_IT,
        closed=CLOSED_IT,
        delimiters=DELIMITERS_IT,
    )


class PizzalongaAwayITSpider(JSONBlobSpider):
    name = "pizzalonga_away_it"
    item_attributes = {
        "brand": "Pizzalonga Away",
        "name": "Pizzalonga Away",
    }
    start_urls = ["https://www.pizzalongaway.it/locali"]
    no_refs = True

    def extract_json(self, response):
        script = response.xpath('//script[contains(text(), "const pois = ")]/text()').get()
        pois = script.split("const pois = ")[-1].split("for (let i =")[0]
        return chompjs.parse_js_object(pois)

    def pre_process_data(self, location):
        location["lat"], location["lon"] = re.findall(r"(\d+\.\d+)", location["position"])
        location["address"] = location.pop("caddress")
        location["phone"] = location.pop("cphone")

    def post_process_item(self, item, response, location):
        apply_category(Categories.FAST_FOOD, item)
        apply_category({"cuisine": "pizza", "takeaway": "only"}, item)
        item["city"] = item["branch"] = item.pop("name")

        item["opening_hours"] = OpeningHours()
        hours = location["copenings"].replace("<br/>", " ").replace("|", ",")
        add_it_ranges(item["opening_hours"], hours)

        deliver = OpeningHours()
        delivery = location["cdelivery"].replace("<br/>", " ").replace("|", ",")
        add_it_ranges(deliver, delivery)
        if deliver:
            item["extras"]["delivery"] = deliver.as_opening_hours()
        else:
            apply_yes_no("delivery", item, False, False)

        yield item
