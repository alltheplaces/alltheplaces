import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser

# Most locations share this central booking/answering number (each with a different
# extension), so it doesn't identify a specific branch and is dropped rather than kept.
SHARED_PHONE_DIGITS = "6156004756"


class FrothyMonkeyUSSpider(SitemapSpider):
    name = "frothy_monkey_us"
    item_attributes = {"brand": "Frothy Monkey"}
    allowed_domains = ["frothymonkey.com"]
    sitemap_urls = ["https://frothymonkey.com/location-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/$", "parse")]

    def parse(self, response: Response):
        address_lines = response.xpath('//div[@class="location-address"]//text()').getall()
        hours_text = " ".join(response.xpath('//div[@class="location-hours"]//text()').getall())
        if not address_lines or "not open to the public" in hours_text:
            # Not a real café location page, e.g. the roasting facility page which is
            # "by appointment only, not open to the public".
            return

        item = Feature()
        item["ref"] = item["website"] = response.url
        item["street_address"] = address_lines[0].strip()
        if len(address_lines) > 1 and (m := re.match(r"(.+?),\s*([A-Z]{2})\s*(\d{5})", address_lines[1].strip())):
            item["city"], item["state"], item["postcode"] = m.groups()

        # Coordinates and the full branch name come from the location's own JSON-LD entry.
        # The page also has a generic Organization/Restaurant entry with no address which
        # must be skipped, and one location (Homewood, at time of writing) has no
        # location-specific JSON-LD at all, so is left without coordinates.
        for ld in LinkedDataParser.iter_linked_data(response):
            types = ld.get("@type")
            types = types if isinstance(types, list) else [types]
            if "Restaurant" in types and "Organization" not in types:
                if geo := ld.get("geo"):
                    item["lat"] = geo.get("latitude")
                    item["lon"] = geo.get("longitude")
                item["name"] = ld.get("name")
                break

        if not item.get("name"):
            title = response.xpath('//h1[@class="entry-title"]/text()').get("").strip()
            item["name"] = f"Frothy Monkey {title}"

        if phone := response.xpath('//div[@class="location-phone"]/p/text()').get():
            phone = phone.strip()
            if re.sub(r"\D", "", phone)[:10] != SHARED_PHONE_DIGITS:
                item["phone"] = phone

        if hours_text:
            item["opening_hours"] = self.parse_hours(hours_text)

        apply_category(Categories.COFFEE_SHOP, item)
        yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        text = text.replace("\xa0", " ")
        if m := re.search(r"Open Daily\s*([\d: ]+[ap]m)\s*[-–—]\s*([\d: ]+[ap]m)", text, re.I):
            oh = OpeningHours()
            oh.add_days_range(DAYS, m.group(1).strip(), m.group(2).strip(), time_format="%I %p")
            return oh
        return None
