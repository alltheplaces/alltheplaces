class EmailCleanUpPipeline:
    def process_item(self, item, spider):
        emails = item.get("email")

        if not emails:
            return item

        if not isinstance(emails, str):
            spider.crawler.stats.inc_value("atp/field/email/wrong_type")
            return item

        for email in emails.split("; "):
            item["email"] = self.normalize(email, spider)
        return item

    def normalize(self, email, spider):
        if "@" not in email:
            spider.crawler.stats.inc_value("atp/field/email/invalid")
            return None
        if email.startswith("mailto:"):
            return email.removeprefix("mailto:")
        return email
