from locations.storefinders.yext import YextSpider


class AutozoneUSSpider(YextSpider):
    name = "autozone_us"
    item_attributes = {"brand": "AutoZone", "brand_wikidata": "Q4826087"}
    drop_attributes = {"email", "twitter"}
    api_key = "a427dc0cb3e4f080da0ebe74621b8020"

    def parse_item(self, item, location, **kwargs):
        item.pop("name", None)
        item["extras"].pop("contact:instagram", None)
        if item.get("facebook") in {"https://www.facebook.com/AutozoneMexico", "https://www.facebook.com/autozone"}:
            del item["facebook"]
        yield item
