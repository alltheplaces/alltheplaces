import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The brand has no locations page; its contact page lists each kennel as a
# heading followed by an icon list holding the address, phone and email.
#
# One kennel gives only a street, with no city line.
#
# No coordinates or hours are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")
# One kennel runs its street into the city with no comma between them.
ADDRESS_NO_COMMA = re.compile(r"(.+?\.)\s+([A-Za-z ]+),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class BarkingHoundVillageUSSpider(Spider):
    name = "barking_hound_village_us"
    item_attributes = {"brand": "Barking Hound Village"}
    allowed_domains = ["www.barkinghoundvillage.com"]
    start_urls = ["https://www.barkinghoundvillage.com/contact-us/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for entry in response.xpath('//ul[contains(@class, "elementor-icon-list-items")]'):
            lines = [
                re.sub(r"\s+", " ", " ".join(line.xpath(".//text()").getall())).strip()
                for line in entry.xpath('.//span[contains(@class, "elementor-icon-list-text")]')
            ]
            lines = [line for line in lines if line]
            if not lines or "@barkinghoundvillage.com" not in " ".join(lines):
                continue

            branch = re.sub(
                r"\s+", " ", entry.xpath("string(./preceding::*[self::h2 or self::h3][1])").get("")
            ).strip()
            if not branch:
                continue

            item = Feature()
            item["branch"] = branch.title()
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", branch.lower()).strip("-")
            item["website"] = response.url

            if address := next((ADDRESS.fullmatch(line) for line in lines if ADDRESS.fullmatch(line)), None):
                item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
            elif address := next(
                (ADDRESS_NO_COMMA.fullmatch(line) for line in lines if ADDRESS_NO_COMMA.fullmatch(line)), None
            ):
                # "2566 East Piedmont Rd. Marietta, GA 30062"
                item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
            else:
                # "1918 Cheshire Bridge Rd." with no city line.
                item["street_address"] = next(
                    (line for line in lines if re.match(r"\d", line) and not PHONE.fullmatch(line)), None
                )
            if not item.get("street_address"):
                continue

            if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
                item["phone"] = phone.group(0)
            item["email"] = next((line for line in lines if "@" in line), None)

            apply_category(Categories.ANIMAL_BOARDING, item)
            item["extras"]["shop"] = "pet_grooming"

            yield item
