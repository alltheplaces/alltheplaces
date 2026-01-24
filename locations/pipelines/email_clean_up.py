import re

from scrapy import Spider
from scrapy.crawler import Crawler

from locations.items import Feature


class EmailCleanUpPipeline:
    crawler: Crawler

    MAILTO_PATTERN = re.compile(r"mailto:", re.IGNORECASE)

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        emails = item.get("email")

        if not emails:
            return item

        if not isinstance(emails, str):
            if self.crawler.stats:
                self.crawler.stats.inc_value("atp/field/email/wrong_type")
            return item

        normalized_emails = []
        for email in emails.split("; "):
            if normalized_email := self.normalize(email, self.crawler.spider):
                normalized_emails.append(normalized_email)
        if normalized_emails == []:
            item["email"] = None
        else:
            item["email"] = ";".join(normalized_emails)
        return item

    def normalize(self, email: str, spider: Spider | None) -> str | None:
        email = self.MAILTO_PATTERN.sub("", email).strip()
        if not email:
            return None
        if "@" not in email:
            if spider and spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/email/invalid")
            return None
        return email
