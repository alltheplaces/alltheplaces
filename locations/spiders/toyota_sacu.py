from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES

BRANDS = {
    "toyotaSupplier": TOYOTA_SHARED_ATTRIBUTES,
    "lexusSupplier": {"brand": "Lexus", "brand_wikidata": "Q35919"},
    "hinoSupplier": {"brand": "Hino Motors", "brand_wikidata": "Q867667"},
}


class ToyotaSacuSpider(JSONBlobSpider):
    name = "toyota_sacu"
    start_urls = ["https://api-toyota.azure-api.net/suppliers?filter[where][supplierType]=dealer"]

    def post_process_item(self, item, response, location):
        brands = []
        brands_wikidata = []
        for brand, attributes in BRANDS.items():
            if location[brand] == "Y":
                brands.append(attributes["brand"])
                brands_wikidata.append(attributes["brand_wikidata"])
        item["brand"] = ";".join(brands)
        item["brand_wikidata"] = ";".join(brands_wikidata)
        if location["serviceOnly"] == "Y":
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        elif item["brand"] == "Hino Motors":
            apply_category(Categories.SHOP_TRUCK, item)
        else:
            apply_category(Categories.SHOP_CAR, item)
        item["website"] = "https://www.toyota.co.za/dealership/" + location["name"].lower().replace(" ", "-")
        if item["state"] in ["Botswana", "Lesotho", "Eswatini", "Namibia"]:
            item["country"] = item.pop("state")
        else:
            item["country"] = "ZA"
        yield item
