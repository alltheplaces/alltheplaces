import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AishasSalonAndSpaUSSpider(Spider):
    name = "aishas_salon_and_spa_us"
    item_attributes = {"brand": "Aisha's Salon & Spa"}
    allowed_domains = ["www.aishassalonandspa.com"]
    start_urls = ["https://www.aishassalonandspa.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath('//div[contains(@class, "wixui-column-strip__column")][.//h2]'):
            lines = [self.clean_text(value) for value in location.xpath(".//p").xpath("string(.)").getall()]
            lines = [line for line in lines if line and not line.startswith("[")]
            try:
                hours_index = next(index for index, line in enumerate(lines) if line.startswith("Monday"))
            except StopIteration:
                continue

            address = ", ".join(lines[1:hours_index])
            if not (address_match := re.search(r"\b([A-Z]{2})\s+(\d{5})\b", address)):
                continue

            branch = location.xpath("normalize-space(.//h2[1])").get()
            item = Feature(
                ref=re.sub(r"[^a-z0-9]+", "-", branch.lower()).strip("-"),
                branch=branch,
                addr_full=address,
                state=address_match.group(1),
                postcode=address_match.group(2),
                country="US",
                phone=lines[0],
                website=response.url,
            )

            hours = OpeningHours()
            for rule in lines[hours_index:]:
                rule = rule.replace(" through ", " - ")
                rule = re.sub(
                    r"(\d{1,2})\s*-\s*(\d{1,2})",
                    lambda match: f"{match.group(1)} {'PM' if match.group(1) == '12' else 'AM'} - {match.group(2)} PM",
                    rule,
                )
                hours.add_ranges_from_string(rule)
            item["opening_hours"] = hours

            apply_category(Categories.SHOP_BEAUTY, item)
            yield item

    @staticmethod
    def clean_text(value: str) -> str:
        return re.sub(r"[\s\u200b]+", " ", value).strip()
