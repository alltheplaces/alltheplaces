import re
from typing import Any

import phonenumbers
from phonenumbers import NumberParseException
from scrapy import Spider
from scrapy.crawler import Crawler

from locations.items import Feature


class PhoneCleanUpPipeline:
    crawler: Crawler

    TEL_PATTERN = re.compile(r"tel:", re.IGNORECASE)
    UNDEFINED_PATTERN = re.compile(r"undefined", re.IGNORECASE)
    NA_PATTERN = re.compile(r"n/a", re.IGNORECASE)
    NUMBERS_ONLY_PATTERN = re.compile(r"[^\d]")
    PHONE_SPLIT_PATTERN = re.compile(r"[;/]\s")

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature) -> Feature:
        phone, country = item.get("phone"), item.get("country")
        extras = item.get("extras", {})
        for key in filter(self.is_phone_key, extras.keys()):
            if not extras[key]:
                continue
            extras[key] = self.normalize_numbers(extras[key], country, self.crawler.spider)

        if not phone:
            return item

        if isinstance(phone, int):
            phone = str(phone)
        elif not isinstance(phone, str):
            self.crawler.stats.inc_value("atp/field/phone/wrong_type")  # ty: ignore[possibly-missing-attribute]
            return item
        item["phone"] = self.normalize_numbers(phone, country, self.crawler.spider)
        return item

    @staticmethod
    def is_phone_key(tag: str) -> bool:
        return (
            tag in ("phone", "fax", "contact:sms", "contact:whatsapp") or tag.endswith(":phone") or tag.endswith(":fax")
        )

    def normalize_numbers(self, phone: str, country: Any, spider: Spider | None) -> str | None:
        numbers = [self.normalize(p, country, spider) for p in self.PHONE_SPLIT_PATTERN.split(str(phone))]
        seen = set()
        phones = []
        for p in numbers:
            if p is not None and p not in seen:
                seen.add(p)
                phones.append(p)
        return ";".join(phones)

    def normalize(self, phone: str, country: Any, spider: Spider | None) -> str | None:
        phone = self.TEL_PATTERN.sub("", phone)
        phone = self.UNDEFINED_PATTERN.sub("", phone)
        phone = self.NA_PATTERN.sub("", phone)
        phone = phone.strip()
        if not phone:
            return None
        numbers_only = self.NUMBERS_ONLY_PATTERN.sub("", phone)
        if numbers_only == "" or int(numbers_only) == 0:
            return None
        try:
            ph = phonenumbers.parse(phone, country)
            if phonenumbers.is_valid_number(ph):
                return phonenumbers.format_number(ph, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except NumberParseException:
            pass
        spider.crawler.stats.inc_value("atp/field/phone/invalid")  # ty: ignore [possibly-missing-attribute]
        return phone
