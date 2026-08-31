import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TheBigBiscuitUSSpider(Spider):
    name = "the_big_biscuit_us"
    item_attributes = {"brand": "The Big Biscuit", "brand_wikidata": "Q124125449"}
    start_urls = ["https://bigbiscuit.com/locations/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs):
        for block in response.css("div.col.w-full.mb-8.lg\\:w-1\\/3"):
            texts = [t.strip() for t in block.css("p, h4").xpath("normalize-space()").getall() if t.strip()]
            if not texts or "coming soon" in " ".join(texts).lower():
                continue

            item = Feature()

            # Branch name is in an h4
            item["branch"] = block.css("h4").xpath("normalize-space()").get("").strip().title()

            # Phone from tel: link
            if phone := block.css("a[href^='tel:']::attr(href)").get():
                item["phone"] = phone.replace("tel:", "")

            # Website from detail link if present
            if detail := block.css("a[href*='bigbiscuit.com']::attr(href)").get():
                item["website"] = detail

            # Coords from Google Maps link
            if maps_url := block.css("a[href*='google.com/maps']::attr(href)").get():
                if m := re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", maps_url):
                    item["lat"], item["lon"] = m.group(1), m.group(2)

            # Address: first non-empty <p> that's not a phone/link
            addr_lines = []
            for p in block.css("p"):
                text = p.xpath("normalize-space()").get("").strip()
                if text and not p.css("a") and text not in (item.get("branch", ""),):
                    addr_lines.append(text)
            if addr_lines:
                # First line is street, second is city/state
                item["street_address"] = addr_lines[0] if len(addr_lines) > 0 else None
                if len(addr_lines) > 1:
                    city_state = addr_lines[1].split(",")
                    item["city"] = city_state[0].strip()
                    if len(city_state) > 1:
                        item["state"] = city_state[1].strip()
                item["country"] = "US"

            item["ref"] = item.get("website") or item["branch"]

            # Opening hours are the same for all stores per FAQ
            oh = OpeningHours()
            oh.add_days_range(DAYS, "06:30", "14:30")
            item["opening_hours"] = oh

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"

            yield item
