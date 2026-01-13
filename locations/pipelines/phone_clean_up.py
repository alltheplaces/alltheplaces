import re

import phonenumbers
from phonenumbers import NumberParseException
from scrapy.crawler import Crawler

from locations.items import Feature


class PhoneCleanUpPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
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
    def is_phone_key(tag):
        return (
            tag in ("phone", "fax", "contact:sms", "contact:whatsapp") or tag.endswith(":phone") or tag.endswith(":fax")
        )

    def normalize_numbers(self, phone, country, spider):
        numbers = [self.normalize(p, country, spider) for p in re.split(r"[;/]\s", str(phone))]
        phones = []
        [phones.append(p) for p in filter(None, numbers) if p not in phones]
        return ";".join(phones)

    def normalize(self, phone, country, spider):
        phone = re.sub(r"tel:", "", phone, flags=re.IGNORECASE)
        phone = re.sub(r"undefined", "", phone, flags=re.IGNORECASE)
        phone = re.sub(r"n/a", "", phone, flags=re.IGNORECASE)
        phone = phone.strip()
        if not phone:
            return None
        numbers_only = re.sub(r"[^\d]", "", phone)
        if numbers_only == "" or int(numbers_only) == 0:
            return None
        try:
            ph = phonenumbers.parse(phone, country)
            if phonenumbers.is_valid_number(ph):
                return phonenumbers.format_number(ph, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except NumberParseException:
            pass
        spider.crawler.stats.inc_value("atp/field/phone/invalid")
        return phone
