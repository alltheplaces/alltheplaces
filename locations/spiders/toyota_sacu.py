from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaSacuSpider(JSONBlobSpider):
    name = "toyota_sacu"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = [
        "https://api-toyota.azure-api.net/suppliers?filter[where][supplierType]=dealer&filter[where][toyotaSupplier]=Y"
    ]

    def post_process_item(self, item, response, location):
        if location["serviceOnly"] == "Y":
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            apply_category(Categories.SHOP_CAR, item)
        item["website"] = "https://www.toyota.co.za/dealership/" + location["name"].lower().replace(" ", "-")
        if item["state"] in ["Botswana", "Lesotho", "Eswatini", "Namibia"]:
            item["country"] = item.pop("state")
        else:
            item["country"] = "ZA"
        yield item
