import re

from scrapy import Spider

from locations.items import Feature


class EmailCleanUpPipeline:
    MAILTO_PATTERN = re.compile(r"mailto:", re.IGNORECASE)

    def process_item(self, item: Feature, spider: Spider) -> Feature:
        emails = item.get("email")

        if not emails:
            return item

        if not isinstance(emails, str):
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/email/wrong_type")
            return item

        normalized_emails = []
        for email in emails.split("; "):
            if normalized_email := self.normalize(email, spider):
                normalized_emails.append(normalized_email)
        if normalized_emails == []:
            item["email"] = None
        else:
            item["email"] = ";".join(normalized_emails)
        return item

    def normalize(self, email: str, spider: Spider) -> str | None:
        email = self.MAILTO_PATTERN.sub("", email).strip()
        if not email:
            return None
        if "@" not in email:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/email/invalid")
            return None
        return email
