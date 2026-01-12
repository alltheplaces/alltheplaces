import re

from scrapy.crawler import Crawler

from locations.items import Feature


class EmailCleanUpPipeline:
    crawler: Crawler

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        emails = item.get("email")

        if not emails:
            return item

        if not isinstance(emails, str):
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

    def normalize(self, email, spider):
        email = re.sub(r"mailto:", "", email, flags=re.IGNORECASE)
        email = email.strip()
        if not email:
            return None
        if "@" not in email:
            spider.crawler.stats.inc_value("atp/field/email/invalid")
            return None
        return email.strip()
