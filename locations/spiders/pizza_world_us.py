import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page lists each restaurant as an info list item holding the
# branch as a heading and the street, "city, state" and phone as lines below.
#
# Restaurants that have not opened are marked "Coming Soon" and carry no phone
# or full address.
#
# The page publishes no postcodes, coordinates or hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class PizzaWorldUSSpider(Spider):
    name = "pizza_world_us"
    item_attributes = {"brand": "Pizza World"}
    allowed_domains = ["www.pizzaworldonline.com"]
    start_urls = ["https://www.pizzaworldonline.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//li[contains(@class, "uabb-info-list-item")]'):
            lines = [
                re.sub(r"\s+", " ", line).strip()
                for line in location.xpath('.//div[contains(@class, "uabb-info-list-description")]//text()').getall()
                if line.strip()
            ]
            # The ordering button below the item reads "Coming Soon" for
            # restaurants that have not opened.
            button = location.xpath(
                'string(./ancestor::div[contains(@class, "fl-col")][1]//span[@class="fl-button-text"])'
            ).get("")
            if "coming soon" in button.lower():
                continue

            # "Odessa, FL", or "Ruskin Fl" without the comma.
            locality = next(
                (
                    match
                    for line in lines
                    if (match := re.fullmatch(r"(.+?),?\s+([A-Za-z]{2})", line)) and match.group(2).isalpha()
                ),
                None,
            )
            if not locality:
                continue

            item = Feature()
            item["branch"] = re.sub(
                r",\s*[A-Za-z]{2}$",
                "",
                location.xpath('.//h2[contains(@class, "uabb-info-list-title")]/text()').get("").strip(),
            )
            item["city"], item["state"] = locality.group(1).strip(), locality.group(2).upper()
            item["street_address"] = ", ".join(lines[: lines.index(locality.group(0))])
            item["ref"] = re.sub(r"[^a-z0-9]+", "-", item["branch"].lower()).strip("-")

            if phone := next((line for line in lines if re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", line)), None):
                item["phone"] = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", phone).group(0)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "pizza"

            yield item
