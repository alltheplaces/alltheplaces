from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.storefinders.woosmap import WoosmapSpider


class EtamSpider(WoosmapSpider):
    name = "etam"
    item_attributes = {"brand": "Etam", "brand_wikidata": "Q3059202"}
    key = "woos-aba9be65-0b4d-3d7e-8baf-5fdc7998a036"
    origin = "https://www.etam.com"

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name").replace("ETAM ", "")
        oh = OpeningHours()
        for day, rules in feature["properties"].get("opening_hours", {}).get("usual", {}).items():
            for hours in rules:
                if hours.get("all-day"):
                    start = "00:00"
                    end = "23:59"
                else:
                    if hours["start"] != "00:00" and hours["end"] != "00:00":
                        start = hours["start"]
                        end = hours["end"]
                    else:
                        continue
                oh.add_range(DAYS[int(day) - 1], start, end)
        item["opening_hours"] = oh.as_opening_hours()
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
