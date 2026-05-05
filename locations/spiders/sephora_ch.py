import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SephoraCHSpider(Spider):
    name = "sephora_ch"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    start_urls = ["https://www.sephora.ch/storefinder/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//div[contains(@class, "storefinder-ch")]//div[contains(@class, "richtext")]'):
            h4 = store.xpath(".//h4/text() | .//h4//text()").getall()
            name = " ".join(h4).strip()
            if not name:
                continue

            paragraphs = [text for p in store.xpath(".//p") if (text := p.xpath("string(.)").get("").strip())]

            item = Feature()
            item["ref"] = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", name.lower())).strip("-")
            item["branch"] = name.removeprefix("CORNER ").removeprefix("STORE ").title()
            item["country"] = "CH"

            self._parse_details(item, paragraphs)
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item

    def _parse_details(self, item: Feature, paragraphs: list[str]) -> None:
        oh = OpeningHours()
        in_hours = False

        for text in paragraphs:
            clean = text.replace("\u200b", "").replace("\ufeff", "").strip()
            if not clean:
                continue

            if "ffnungszeiten" in clean:
                in_hours = True
                # Hours text may follow on the same line after the colon
                after_colon = clean.split(":", 1)[-1].strip() if ":" in clean else ""
                if after_colon and re.search(r"\d{1,2}:\d{2}", after_colon):
                    self._add_hours(oh, after_colon)
                continue

            if in_hours and re.search(r"\d{1,2}:\d{2}", clean):
                self._add_hours(oh, clean)
                continue

            if in_hours:
                continue

            if re.match(r"^\+41\s", clean):
                item["phone"] = clean
            elif re.match(r"^\d{4}\s", clean):
                parts = clean.split(" ", 1)
                item["postcode"] = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
                rest = rest.removesuffix(" Switzerland").strip()
                item["city"] = rest
            elif not item.get("street_address"):
                item["street_address"] = clean

        item["opening_hours"] = oh

    @staticmethod
    def _add_hours(oh: OpeningHours, text: str) -> None:
        try:
            oh.add_ranges_from_string(text, days=DAYS_DE)
        except Exception:
            pass
