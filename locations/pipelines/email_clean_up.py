class EmailCleanUpPipeline:
    def process_item(self, item, spider):
        emails = item.get("email")

        if not emails:
            return item

        if not isinstance(emails, str):
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

    def normalize(self, email, spider):
        if "@" not in email:
            spider.crawler.stats.inc_value("atp/field/email/invalid")
            return None
        if email.startswith("mailto:"):
            return email.removeprefix("mailto:")
        return email.strip()
