import re
from typing import Any, Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The locations page builds its map from a series of pointMapJSON.push({...})
# calls in an inline script, one per restaurant, each with a title, coordinates
# and an info window description built by concatenating string literals. The
# description holds the address, phone and the restaurant's own page.
#
# One restaurant is marked "(Temporarily Closed)" in its title and is skipped.
# No opening hours are published on this page.


class RodizioGrillUSSpider(Spider):
    name = "rodizio_grill_us"
    item_attributes = {"brand": "Rodizio Grill", "brand_wikidata": "Q97354436"}
    allowed_domains = ["www.rodiziogrill.com"]
    start_urls = ["https://www.rodiziogrill.com/locations.aspx"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for block in re.findall(r"pointMapJSON\.push\(\{(.*?)\}\);", response.text, re.S):
            title = self.field(block, "title")
            if not title or "temporarily closed" in title.lower():
                continue

            # The description is several string literals joined with "+".
            description = Selector(
                text="".join(re.findall(r"'((?:[^'\\]|\\.)*)'", block.split("'description':", 1)[-1]))
            )

            item = Feature()
            item["branch"] = re.sub(r"^Rodizio Grill\s*(?:-\s*)?", "", title).strip()
            item["lat"] = self.field(block, "lat", quoted=False)
            item["lon"] = self.field(block, "lng", quoted=False)
            item["phone"] = description.xpath('//a[starts-with(@href, "tel:")]/text()').get()
            item["website"] = description.xpath('//span[@class="moreInfoLink"]/a/@href').get()
            item["ref"] = (item["website"] or title).rstrip("/").rsplit("/", 1)[-1]

            # "1840 S Val Vista Dr.<br>Mesa, AZ 85204<br><a href=tel:...>"
            lines = [line.strip() for line in description.xpath("//div/div/text()").getall() if line.strip()]
            for index, line in enumerate(lines):
                if locality := re.fullmatch(r"(.+?),\s*([A-Z]{2})\s+(\d{5})", line):
                    item["city"], item["state"], item["postcode"] = locality.groups()
                    item["street_address"] = merge_address_lines(lines[:index])
                    break

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "brazilian;steak_house"

            yield item

    @staticmethod
    def field(block: str, name: str, quoted: bool = True) -> str | None:
        pattern = rf"'{name}':\s*'([^']*)'" if quoted else rf"'{name}':\s*(-?[\d.]+)"
        return match.group(1) if (match := re.search(pattern, block)) else None
