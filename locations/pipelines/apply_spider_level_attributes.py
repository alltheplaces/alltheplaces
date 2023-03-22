class ApplySpiderLevelAttributesPipeline:
    def process_item(self, item, spider):
        if not hasattr(spider, "item_attributes"):
            return item

        item_attributes = spider.item_attributes

        for key, value in item_attributes.items():
            if key == "extras":
                extras = item.get("extras", {})
                for k, v in value.items():
                    if extras.get(k) is None:
                        extras[k] = v
                item["extras"] = extras
            else:
                if item.get(key) is None:
                    item[key] = value

        return item
