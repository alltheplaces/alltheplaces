import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_EN, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


def normalise_time(raw: str) -> str:
    raw = raw.lower().replace(" ", "").replace(".", "")
    if ":" not in raw:
        raw = raw.replace("am", ":00am").replace("pm", ":00pm")
    hour, rest = raw.split(":")
    minute, meridiem = rest[:2], rest[2:]
    hour = int(hour) % 12
    if meridiem == "pm":
        hour += 12
    return f"{hour:02d}:{minute}"


class FarewayUSSpider(Spider):
    name = "fareway_us"
    item_attributes = {"brand": "Fareway", "brand_wikidata": "Q5434998"}
    start_urls = ["https://www.fareway.com/stores"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.url.rstrip("/") == "https://www.fareway.com/stores":
            for page_url in response.css("ul.page-selection-list a::attr(href)").getall():
                if not page_url.endswith("/page/1"):
                    yield response.follow(page_url, callback=self.parse)

        for card in response.css("div.card.store"):
            hours_text = " ".join(t.strip() for t in card.css(".store-hours *::text").getall() if t.strip())
            if "coming soon" in hours_text.lower():
                # Store not yet open for business.
                continue

            store_url = card.css("h3.card-title a::attr(href)").get()
            address = " ".join(card.css("p.card-subtitle a::text").getall()).strip()
            address_parts = [part.strip() for part in address.split(",")]
            state, _, postcode = address_parts[-1].partition(" ")
            city = address_parts[-2]
            if city.isupper():
                city = city.title()

            item = Feature()
            item["ref"] = store_url.rsplit("/", 1)[-1]
            item["lat"] = card.attrib.get("data-latitude")
            item["lon"] = card.attrib.get("data-longitude")
            item["street_address"] = ", ".join(address_parts[:-2])
            item["city"] = city
            item["state"] = state
            item["postcode"] = postcode
            item["phone"] = card.css(".store-phone a::text").get()
            item["website"] = response.urljoin(store_url)
            item["branch"] = city
            item["facebook"] = card.css("a.store-card-facebook-link::attr(href)").get()

            # Every store's hours follow "<day range> (closed <day>) <time range>",
            # with an occasional extra note about a separate carry-out window that
            # is not the store's own opening hours, so anything after it is dropped.
            hours_text = re.split(r"carry out", hours_text, flags=re.I)[0]
            closed_day_match = re.search(r"closed\s+([a-z]+)", hours_text, re.I)
            hours_text = re.sub(r"\([^)]*\)", "", hours_text)
            day_match = re.search(r"([a-z]+)\s*-\s*([a-z]+)", hours_text, re.I)
            time_match = re.search(
                r"(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)", hours_text, re.I
            )
            if day_match and time_match and (start_day := DAYS_EN.get(day_match.group(1).title())):
                if end_day := DAYS_EN.get(day_match.group(2).title()):
                    days = DAYS[DAYS.index(start_day) : DAYS.index(end_day) + 1]
                    oh = OpeningHours()
                    oh.add_days_range(days, normalise_time(time_match.group(1)), normalise_time(time_match.group(2)))
                    if closed_day_match and (closed_day := DAYS_EN.get(closed_day_match.group(1).title())):
                        oh.set_closed(closed_day)
                    item["opening_hours"] = oh

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
