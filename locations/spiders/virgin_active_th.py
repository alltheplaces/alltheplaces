from chompjs import parse_js_object

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import get_merged_item
from locations.spiders.virgin_active_sg import VirginActiveSGSpider


class VirginActiveTHSpider(VirginActiveSGSpider):
    name = "virgin_active_th"
    start_urls = ["https://www.virginactive.co.th/locations", "https://www.virginactive.co.th/en/locations"]
    stored_items = {}

    def parse_location(self, response):
        item = response.meta["item"]
        location = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]
        item["website"] = response.url
        item["email"] = location["email"]
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for day in location["openingHours"]:
            if day["value"].lower() == "closed" and day["label"] in DAYS_3_LETTERS:
                item["opening_hours"].set_closed(day["label"])
            else:
                item["opening_hours"].add_ranges_from_string(day["label"] + " " + day["value"])

        if item["ref"] in self.stored_items:
            other_item = self.stored_items.pop(item["ref"])
            if "/en/" in response.url:
                # TH opening hours are not parsed, so copy them over
                other_item["opening_hours"] = item["opening_hours"]
                item["lat"] = other_item["lat"]
                item["lon"] = other_item["lon"]  # Slightly different location for some items, for some reason
                yield get_merged_item({"en": item, "th": other_item}, "th")
            else:
                # TH opening hours are not parsed, so copy them over
                item["opening_hours"] = other_item["opening_hours"]
                other_item["lat"] = item["lat"]
                other_item["lon"] = item["lon"]  # Slightly different location for some items, for some reason
                yield get_merged_item({"en": other_item, "th": item}, "th")

        else:
            self.stored_items[item["ref"]] = item
