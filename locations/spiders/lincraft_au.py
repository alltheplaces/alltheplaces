from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class LincraftAUSpider(StockistSpider):
    name = "lincraft_au"
    item_attributes = {"brand": "Lincraft", "brand_wikidata": "Q17052417"}
    key = "u6788"

    def parse_item(self, item, location):
        item["website"] = location["custom_fields"][0]["value"].replace("lincraftau.myshopify.com", "lincraft.com.au")
        oh = OpeningHours()
        hours_raw = (
            " ".join(location["description"].split())
            .replace("Store Trading Hours", "")
            .replace("9am-10am-5pm", "10am-5pm")
            .replace("-", " ")
            .split()
        )
        hours_raw = hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            open_time = day[1].upper()
            if ":" not in open_time:
                open_time = open_time.replace("AM", ":00AM").replace("PM", ":00PM")
            close_time = day[2].upper()
            if ":" not in close_time:
                close_time = close_time.replace("AM", ":00AM").replace("PM", ":00PM")
            oh.add_range(day[0], open_time, close_time, "%I:%M%p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
