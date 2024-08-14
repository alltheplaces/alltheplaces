from locations.storefinders.storemapper import StoremapperSpider


class VpzGBSpider(StoremapperSpider):
    name = "vpz_gb"
    item_attributes = {"brand": "VPZ", "brand_wikidata": "Q107300487"}
    company_id = "14072-3UOwEWhgZ0NnwVEo"

    def parse_item(self, item, location):
        for custom_field in location["store_custom_fields"]:
            if custom_field["custom_field_id"] == 42770:
                item["city"] = custom_field["value"]
            if custom_field["custom_field_id"] == 42771:
                item["state"] = custom_field["value"]
        item.pop("website")
        item.pop("email")
        yield item
