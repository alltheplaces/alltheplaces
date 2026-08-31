import re
from hashlib import sha1

import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_BG, DELIMITERS_EN, OpeningHours
from locations.items import Feature


class RoisBGSpider(scrapy.Spider):
    name = "rois_bg"
    item_attributes = {"brand": "Rois", "brand_wikidata": "Q110399902", "country": "BG"}
    allowed_domains = ["www.rois.bg"]
    start_urls = ["https://www.rois.bg/pekarni"]

    def parse(self, response):
        for store in response.css("div.text-with-preview"):
            paragraphs = []
            for p in store.css("div.text-with-preview__content p"):
                text = " ".join(t.strip() for t in p.xpath(".//text()").getall())
                text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
                if text:
                    paragraphs.append(text)

            address_parts = []
            hours_text = None
            for text in paragraphs:
                if "Работно време" in text:
                    hours_text = text.replace("Работно време", "").strip()
                elif hours_text is None:
                    address_parts.append(text)

            addr_full = ", ".join(address_parts)
            if not addr_full:
                continue

            item = Feature()
            item["ref"] = sha1(addr_full.encode("utf-8")).hexdigest()
            item["branch"] = store.xpath(".//h2/text()").get(default="").strip()
            item["addr_full"] = addr_full
            extract_google_position(item, store)

            if hours_text:
                item["opening_hours"] = self.parse_hours(hours_text)

            apply_category(Categories.SHOP_NUTS, item)

            yield item

    @staticmethod
    def parse_hours(hours_text: str) -> OpeningHours:
        # Site uses "÷" as a day range separator, and "от X до Y" (from X until Y)
        # to express time ranges, instead of the more common "-" delimiter.
        hours_text = hours_text.replace("÷", "-")
        hours_text = re.sub(r"\bот\s+", "", hours_text)
        hours_text = re.sub(r"\s+до\s+", "-", hours_text)

        oh = OpeningHours()
        oh.add_ranges_from_string(hours_text, DAYS_BG, delimiters=DELIMITERS_EN + ["и"])
        return oh
