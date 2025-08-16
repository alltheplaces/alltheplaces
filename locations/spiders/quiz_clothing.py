from locations.json_blob_spider import JSONBlobSpider


class QuizClothingSpider(JSONBlobSpider):
    name = "quiz_clothing"
    item_attributes = {
        "brand_wikidata": "Q29995941",
        "brand": "Quiz",
    }
    start_urls = ["https://www.quizclothing.co.uk/api/inventory/inventoryGetStoreFilter?countryId=0&cityId=0&cityId=0"]
    locations_key = "data"
