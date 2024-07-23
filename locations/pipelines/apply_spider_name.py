class ApplySpiderNamePipeline:
    def process_item(self, item, spider):
        existing_extras = item.get("extras", {})
        existing_extras["spider"] = spider.name
        item["extras"] = existing_extras

        return item
