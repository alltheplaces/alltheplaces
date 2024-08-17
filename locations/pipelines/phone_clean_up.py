import re

import phonenumbers
from phonenumbers import NumberParseException


class PhoneCleanUpPipeline:
    def process_item(self, item, spider):
        phone, country = item.get("phone"), item.get("country")
        extras = item.get("extras", {})
        for key in filter(self.is_phone_key, extras.keys()):
            if not extras[key]:
                continue
            extras[key] = self.normalize_numbers(extras[key], country, spider)

        if not phone:
            return item

        if isinstance(phone, int):
            phone = str(phone)
        elif not isinstance(phone, str):
            spider.crawler.stats.inc_value("atp/field/phone/wrong_type")
            return item
        item["phone"] = self.normalize_numbers(phone, country, spider)
        return item

    @staticmethod
    def is_phone_key(tag):
        return tag in ("phone", "fax") or tag.endswith(":phone") or tag.endswith(":fax")

    def normalize_numbers(self, phone, country, spider):
        numbers = [self.normalize(p, country, spider) for p in re.split(r"[;/]\s", str(phone))]
        return ";".join(filter(None, numbers))

    def normalize(self, phone, country, spider):
        phone = re.sub(r"tel:", "", phone, flags=re.IGNORECASE)
        phone = re.sub(r"undefined", "", phone, flags=re.IGNORECASE)
        phone = re.sub(r"n/a", "", phone, flags=re.IGNORECASE)
        phone = phone.strip()
        if not phone:
            return None
        try:
            ph = phonenumbers.parse(phone, country)
            if phonenumbers.is_valid_number(ph):
                return phonenumbers.format_number(ph, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except NumberParseException:
            pass
        spider.crawler.stats.inc_value("atp/field/phone/invalid")
        return phone
