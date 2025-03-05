import json
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.categories import Categories, apply_category, apply_yes_no

class RedtagFashionAESASpider(Spider):
    name = "redtag_fashion_ae_sa"
    item_attributes = {
        "brand": "Red Tag",
        "brand_wikidata": "Q132891092",
    }

    def start_requests(self):
        countries = ["Saudi Arabia", "UAE"]
        for country in countries:
            yield Request(
                url=f"https://redtagfashion.com/locations/locations.php?country={country}",
                meta={"country": country},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["ref"] = f"{response.meta['country']}_{store['storecode']}"
            item["street_address"] = item.pop("addr_full")

            if hours := store.get("timming"):  # Note the misspelling in the API
                oh = OpeningHours()
                oh.add_ranges_from_string(hours)
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_CLOTHES, item)
            
            apply_yes_no("homeware", item, store.get("homeware") == "1")
            apply_yes_no("cosmetics", item, store.get("cosmetics") == "1")

            yield item

    def parse_hours(self, hours_str: str) -> str:
        """Parse hours string into OpenStreetMap format"""
        if not hours_str:
            return None

        def convert_time(time_str: str) -> str:
            """Convert 12-hour time to 24-hour format"""
            time = time_str.strip()
            if "AM" in time:
                time = time.replace(" AM", "").strip()
                if ":" not in time:
                    time += ":00"
                hour, minute = map(int, time.split(":"))
                hour = 0 if hour == 12 else hour
                return f"{hour:02d}:{minute:02d}"
            elif "PM" in time:
                time = time.replace(" PM", "").strip()
                if ":" not in time:
                    time += ":00"
                hour, minute = map(int, time.split(":"))
                hour = hour if hour == 12 else hour + 12
                return f"{hour:02d}:{minute:02d}"
            if ":" not in time:
                time += ":00"
            return time.strip()

        def format_days(day_str: str) -> str:
            day_map = {
                "SUN": "Su", "MON": "Mo", "TUE": "Tu", "WED": "We", "THU": "Th", "FRI": "Fr", "SAT": "Sa",
                "Sun": "Su", "Mon": "Mo", "Tue": "Tu", "Wed": "We", "Thu": "Th", "Fri": "Fr", "Sat": "Sa"
            }
            day_str = day_str.strip()
            if " to " in day_str:
                start, end = map(str.strip, day_str.split(" to ", 1))
                return f"{day_map.get(start.upper(), start[:2])}-{day_map.get(end.upper(), end[:2])}"
            elif "&" in day_str:
                days = [d.strip() for d in day_str.split("&")]
                return ",".join(day_map.get(d.upper(), d[:2]) for d in days)
            return day_map.get(day_str.upper(), day_str[:2])

        parts = [p.strip() for p in hours_str.replace("|", "*").split("*") if p.strip()]
        result = {}

        for part in parts:
            if not any(day in part.upper() for day in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT", "TO", "&"]):
                times = []
                for time_range in part.split("|"):
                    if " - " in time_range:
                        start, end = map(convert_time, time_range.strip().split(" - "))
                        times.append(f"{start}-{end}")
                day_key = "Mo-Su"
                result[day_key] = result.get(day_key, []) + times
                continue

            day_part = time_part = ""
            if " - " in part:
                match_pos = min((part.find(p) for p in [" AM - ", " PM - ", " - "] if p in part), default=-1)
                if match_pos > 0:
                    space_pos = part[:match_pos].rfind(" ")
                    if space_pos > 0:
                        day_part, time_part = part[:space_pos].strip(), part[space_pos:].strip()

            if not (day_part and time_part):
                for day in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
                    if day in part:
                        pos = part.find(day) + len(day)
                        if pos < len(part) and part[pos] == " ":
                            day_part, time_part = part[:pos].strip(), part[pos:].strip()
                            break

            if not (day_part and time_part) and " " in part:
                day_part, time_part = part.split(" ", 1)

            if day_part and time_part:
                day_key = format_days(day_part)
                times = []
                for time_range in time_part.split("|"):
                    if " - " in time_range:
                        start, end = map(convert_time, time_range.strip().split(" - "))
                        times.append(f"{start}-{end}")
                result[day_key] = result.get(day_key, []) + times

        formatted_hours = []
        for day, times in result.items():
            if times:
                formatted_hours.append(f"{day} {','.join(times)}")

        return "; ".join(formatted_hours) if formatted_hours else None
