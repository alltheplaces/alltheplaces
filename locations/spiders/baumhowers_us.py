import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page is built with Wix and lists each restaurant as three
# consecutive rich text blocks: the branch, the address and the phone.
#
# The address is one line, and three restaurants omit the comma before the
# city.
#
# No coordinates or hours are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([A-Za-z .']+),\s*([A-Z]{2})\s+(\d{5})")
# Three restaurants omit the comma before the city, so the city is matched
# against the branch name instead.
ADDRESS_NO_COMMA = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class BaumhowersUSSpider(Spider):
    name = "baumhowers_us"
    item_attributes = {"brand": "Baumhower's Victory Grille"}
    allowed_domains = ["www.baumhowers.com"]
    start_urls = ["https://www.baumhowers.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        blocks = [
            re.sub(r"\s+", " ", " ".join(block.xpath(".//text()").getall())).strip()
            for block in response.xpath('//div[@data-testid="richTextElement"]')
        ]
        blocks = [block for block in blocks if block]

        for index, block in enumerate(blocks):
            branch = blocks[index - 1].title() if index else ""

            if address := ADDRESS.fullmatch(block):
                street, city, state, postcode = address.groups()
            elif address := ADDRESS_NO_COMMA.fullmatch(block):
                head, state, postcode = address.groups()
                # "31 Marketplace Drive Millbrook, AL 36054"
                if not branch or not head.lower().endswith(branch.lower()):
                    continue
                street, city = head[: -len(branch)].strip(" ,"), branch
            else:
                continue

            item = Feature()
            item["branch"] = branch or None
            item["street_address"], item["city"], item["state"], item["postcode"] = street, city, state, postcode
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{item['branch']} {item['postcode']}".lower()).strip("-")

            if index + 1 < len(blocks) and PHONE.fullmatch(blocks[index + 1]):
                item["phone"] = blocks[index + 1]

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"

            yield item
