from locations.storefinders.yext_answers import YextAnswersSpider


class KateSpadeSpider(YextAnswersSpider):
    name = "kate_spade"
    item_attributes = {"brand": "Kate Spade New York", "brand_wikidata": "Q6375797"}
    api_key = "b7318cda413fa6f985c0770ffb411bbd"
    experience_key = "kate-spade-uk"
