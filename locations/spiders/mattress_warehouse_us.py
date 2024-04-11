from locations.storefinders.yext import YextSpider


class MattressWarehouseUSSpider(YextSpider):
    name = "mattress_warehouse_us"
    item_attributes = {"brand": "Mattress Warehouse", "brand_wikidata": "Q61995079"}
    api_key = "0277c3ad01c944bfc148a777fa36764d"

    def parse_item(self, item, location, **kwargs):
        if item["ref"] in [
            "0000",  # "in regards to your delivery"
            "59",  # HQ
            "6664888033510164995",  # "Test"
        ]:
            return

        if "COMING SOON" in item["name"]:
            return

        item["branch"] = item.pop("name").removeprefix("Mattress Warehouse ").removeprefix("of ").removeprefix("- ")

        yield item
