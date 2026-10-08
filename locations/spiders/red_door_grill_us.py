import re
from collections import Counter
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page gives each restaurant a Divi section holding its name, a
# street address, a phone and a directions link. Each section's content is
# repeated for the desktop and mobile layouts, so the values are deduplicated.
#
# Only one restaurant publishes a city, state and postcode; the rest give the
# street alone.
#
# Coordinates come from the directions link where it is a Google Maps place
# URL, but three sections share one restaurant's link, so a link used by more
# than one section is not trusted.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class RedDoorGrillUSSpider(Spider):
    name = "red_door_grill_us"
    item_attributes = {"brand": "Red Door Woodfired Grill"}
    allowed_domains = ["reddoorgrill.com"]
    start_urls = ["https://reddoorgrill.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        sections = response.xpath('//div[contains(@class, "et_pb_section")]')

        # Several sections reuse another restaurant's directions link, and each
        # section repeats its own, so the links are counted once per section.
        coordinates = Counter()
        for section in sections:
            found = set()
            for link in section.xpath('.//a[contains(@href, "maps")]/@href').getall():
                if match := re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", link):
                    found.add(match.group(0))
            coordinates.update(found)

        for section in sections:
            blurbs = {}
            for blurb in section.xpath('.//div[contains(@class, "et_pb_blurb")]'):
                label = re.sub(r"\s+", " ", " ".join(blurb.xpath(".//h4//text()").getall())).strip()
                value = re.sub(
                    r"\s+", " ", " ".join(blurb.xpath('.//div[contains(@class, "blurb_description")]//text()').getall())
                ).strip()
                if label and value:
                    blurbs.setdefault(label, value)

            if not (address := blurbs.get("Address")):
                continue

            item = Feature()
            # The first heading of one section is a banner, so the last
            # heading names the restaurant.
            headings = [re.sub(r"\s+", " ", heading).strip() for heading in section.xpath(".//h2//text()").getall()]
            headings = [heading for heading in headings if heading]
            branch = headings[-1] if headings else ""
            item["branch"] = (branch.title() if branch.isupper() else branch) or None
            item["website"] = response.url
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{item['branch']} {address}".lower()).strip("-")

            # "6680 Center St, Omaha, NE 68106", or the street on its own.
            if locality := ADDRESS.fullmatch(address):
                item["street_address"], item["city"], item["state"], item["postcode"] = locality.groups()
            else:
                item["street_address"] = address

            if phone := PHONE.fullmatch(blurbs.get("Phone") or ""):
                item["phone"] = phone.group(0)

            # Some sections link the short directions URL before the place URL.
            for link in section.xpath('.//a[contains(@href, "maps")]/@href').getall():
                if (place := re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", link)) and coordinates[place.group(0)] == 1:
                    item["lat"], item["lon"] = place.groups()
                    break

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"

            yield item
