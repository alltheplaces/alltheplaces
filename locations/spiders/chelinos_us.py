import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page lists each restaurant as a block holding the branch as a
# heading and the street, "city, state postcode" and phone as lines below.
#
# The page publishes no coordinates or hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})")


class ChelinosUSSpider(Spider):
    name = "chelinos_us"
    item_attributes = {"brand": "Chelino's Mexican Restaurant"}
    allowed_domains = ["www.chelinos.com"]
    start_urls = ["https://www.chelinos.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for block in response.xpath('//div[contains(@class, "div-block-123")]'):
            lines = [
                re.sub(r"\s+", " ", line).strip() for line in block.xpath(".//strong//text()").getall() if line.strip()
            ]
            locality = next((match for line in lines if (match := ADDRESS.fullmatch(line))), None)
            if not locality:
                continue

            item = Feature()
            item["branch"] = re.sub(r"\s+", " ", block.xpath(".//h1/text()").get("") or "").strip()
            item["city"], item["state"], item["postcode"] = locality.groups()
            item["street_address"] = ", ".join(lines[: lines.index(locality.group(0))])
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", f"{item['branch']} {item['postcode']}".lower()).strip("-")

            if phone := next(
                (line for line in lines if re.fullmatch(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", line)), None
            ):
                item["phone"] = phone

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "mexican"

            yield item
