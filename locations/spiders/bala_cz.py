import json
import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature


class BalaCZSpider(Spider):
    name = "bala_cz"
    item_attributes = {"brand": "Bala"}
    start_urls = ["https://www.mojebala.cz/mapa"]
    custom_settings = {"USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def parse(self, response: Response):
        # All store data is embedded as a JavaScript variable in the page
        raw_js = response.text
        idx = raw_js.find("var contacts = [")
        if idx == -1:
            return
        start = raw_js.index("[", idx)
        depth = 0
        end = start
        for i, c in enumerate(raw_js[start:], start):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        contacts = json.loads(raw_js[start : end + 1])

        for contact in contacts:
            oh = OpeningHours()
            if hours_text := contact.get("oteviraciDoba"):
                # Normalise decimal-comma time format: "7,30" -> "7:30"
                hours_text = re.sub(r"(\d),(\d)", r"\1:\2", hours_text)
                oh.add_ranges_from_string(hours_text, days=DAYS_CZ, delimiters=["−", "-", ";"])

            item = Feature()
            item["ref"] = contact["id"]
            item["name"] = contact.get("nazev")
            item["street_address"] = contact.get("ulice")
            item["city"] = contact.get("mesto")
            item["postcode"] = contact.get("psc")
            item["country"] = "CZ"
            item["lat"] = contact.get("gpsLat")
            item["lon"] = contact.get("gpsLng")
            item["phone"] = contact.get("telefon")
            item["email"] = contact.get("email1")
            if web := contact.get("web"):
                item["website"] = f"http://{web}" if not web.startswith("http") else web
            if oh.as_opening_hours():
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
