import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MarvinsBuildingMaterialsUSSpider(scrapy.Spider):
    name = "marvins_building_materials_us"
    item_attributes = {
        "brand": "Marvin's Building Materials",
        "brand_wikidata": "Q109395525",
    }
    start_urls = ["https://www.marvinsbuildingmaterials.com/locations"]

    def parse(self, response):
        for h6 in response.css("h6.font_6"):
            title = h6.xpath("string(.)").get("").strip()
            if not re.fullmatch(r"[^,]+,\s*[A-Z]{2}", title):
                continue

            container = h6.xpath("ancestor::div[@data-mesh-id][1]")
            paragraphs = [p.xpath("string(.)").get("").strip() for p in container.css("p.font_8")]
            if len(paragraphs) < 1:
                continue

            addr_lines = [line.strip() for line in paragraphs[0].split("\n") if line.strip()]
            if len(addr_lines) < 3:
                continue
            street_address, city_state_zip, phone = addr_lines[0], addr_lines[1], addr_lines[2]

            m = re.match(r"^(?P<city>.+),\s*(?P<state>[A-Z]{2})\s*(?P<postcode>\d{5})$", city_state_zip)
            if not m:
                continue

            item = Feature()
            item["ref"] = title
            item["street_address"] = street_address
            item["city"] = m.group("city")
            item["state"] = m.group("state")
            item["postcode"] = m.group("postcode")
            item["phone"] = phone
            item["website"] = response.url

            if len(paragraphs) > 1:
                details = paragraphs[1]
                hours_text = details.split("Hours:", 1)[-1] if "Hours:" in details else ""
                hours_text = hours_text.replace("M-Sat", "Mon-Sat").replace("\n", " ")
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_text)

            apply_category(Categories.SHOP_DOITYOURSELF, item)

            item["name"] = self.item_attributes["brand"]

            yield item
