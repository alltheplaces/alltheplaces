import re

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature


class MujobchodCZSpider(Spider):
    name = "mujobchod_cz"
    item_attributes = {
        "brand": "Můj obchod",
        "brand_wikidata": "Q130658827",
    }
    start_urls = [
        "https://www.mujobchod.cz/sxa/search/results?s=%7BF2EE6EC1-265E-466C-88DA-EFF88C6451FC%7D&sig=store-locator&v=%7BE28DD955-5695-4D9E-BD32-0C48ED2A443D%7D&p=2500&o=Title%2CAscending&g="
    ]

    def parse(self, response: Response):
        data = response.json()
        for result in data.get("Results", []):
            geo = result.get("Geospatial", {})
            lat = geo.get("Latitude")
            lon = geo.get("Longitude")

            sel = Selector(text=result.get("Html", ""))

            store_id = sel.xpath("//@data-storeid").get()
            name_parts = sel.xpath(".//span[@class='sl-store-name']//text()").getall()
            name = " ".join(p.strip() for p in name_parts if p.strip())
            address_text = sel.xpath("normalize-space(.//a[contains(@href,'google.com/maps')]//text())").get("").strip()

            # Parse address: "Street, City, PostCode"
            addr_parts = [p.strip() for p in address_text.split(",")]
            street_address = addr_parts[0] if len(addr_parts) > 0 else None
            city = addr_parts[1] if len(addr_parts) > 1 else None
            postcode = addr_parts[2] if len(addr_parts) > 2 else None

            # Per-location page URL from "Zjistit více" link
            store_slug = sel.xpath(".//a[contains(@class,'store-info-button')]/@title").get()
            website = f"https://www.mujobchod.cz/obchody/{store_slug}" if store_slug else None

            # Opening hours: rows of day name + time range
            oh = OpeningHours()
            days = sel.xpath(".//div[@class='day-title field-translation']/text()").getall()
            hours = sel.xpath(".//div[contains(@class,'day-hours')]/text()").getall()
            for day_str, hour_str in zip(days, hours):
                day_str = day_str.strip()
                hour_str = hour_str.strip()
                if not day_str or not hour_str:
                    continue
                day = DAYS_CZ.get(day_str)
                if not day:
                    continue
                if re.search(r"zavř|closed", hour_str, re.IGNORECASE):
                    oh.set_closed(day)
                else:
                    # Format: "HH:MM-HH:MM"
                    m = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", hour_str)
                    if m:
                        oh.add_range(day, m.group(1), m.group(2))

            item = Feature()
            item["ref"] = store_id or result.get("Id")
            item["name"] = name
            item["lat"] = lat
            item["lon"] = lon
            item["street_address"] = street_address
            item["city"] = city
            item["postcode"] = postcode
            item["country"] = "CZ"
            item["website"] = website
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
