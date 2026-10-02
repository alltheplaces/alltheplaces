import re

import chompjs
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class OKuSushiUSSpider(Spider):
    name = "o_ku_sushi_us"
    item_attributes = {"brand": "O-Ku Sushi"}
    start_urls = ["https://www.o-kusushi.com/store-locator/"]

    def parse(self, response):
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])
        for location in config["locations"]:
            hours_text = " ".join(Selector(text=location["hours"]).xpath("//text()").getall())
            if "coming soon" in hours_text.lower():
                continue
            item = Feature(
                ref=location["slug"],
                branch=location["name"],
                street_address=location["street"],
                city=location["city"],
                state=location["state"],
                postcode=location["postal_code"],
                country="US",
                lat=location["lat"],
                lon=location["lng"],
                phone=location["phone_number"],
                email=location["email_address"],
                website=response.urljoin(location["url"]),
            )
            # Promotions follow regular hours and must not extend the opening schedule.
            hours_text = re.split(r"(?:Sushi\s+)?Happy Hour", hours_text, flags=re.I)[0]
            hours_text = hours_text.replace("&", "and")
            hours_text = re.sub(r"\b(\d{1,2}) to (\d{1,2}) p\.m\.", r"\1pm to \2pm", hours_text)
            hours = OpeningHours()
            hours.add_ranges_from_string(hours_text)
            if not hours.as_opening_hours():
                for day, ranges in location["structured_hours"].items():
                    for time_range in ranges:
                        hours.add_range(day, time_range["open_time"], time_range["close_time"], time_format="%H:%M:%S")
            item["opening_hours"] = hours
            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "japanese;sushi"
            yield item
