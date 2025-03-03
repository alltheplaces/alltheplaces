from scrapy import Request

from locations.json_blob_spider import JSONBlobSpider


class PetFoodExpressUSSpider(JSONBlobSpider):
    name = "pet_food_express_us"
    item_attributes = {
        "brand": "Pet Food Express",
        "brand_wikidata": "Q7171541",
    }

    def start_requests(self):
        yield Request(
            "https://apis.petfood.express/bigcommerce/store/map/",
            headers={"x-api-key": "5a69a1c9bb55458d8d831768ae2ab349"},
        )

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        yield item
