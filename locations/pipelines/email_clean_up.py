class EmailCleanUpPipeline:
    def process_item(self, item, spider):
        email = item.get("email")

        if not email:
            return item

        if not isinstance(email, str):
            spider.crawler.stats.inc_value("atp/field/email/wrong_type")
            return item

        item["email"] = self.normalize(email, spider)
        return item

    def normalize(self, email, spider):
        if "@" not in email:
            spider.crawler.stats.inc_value("atp/field/email/invalid")
            return None
        return email
