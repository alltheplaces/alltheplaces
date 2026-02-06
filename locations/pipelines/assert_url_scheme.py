from locations.items import Feature


class AssertURLSchemePipeline:
    def process_item(self, item: Feature):
        if item.get("image"):
            if item["image"].startswith("//"):
                item["image"] = "https:" + item["image"]

        return item
