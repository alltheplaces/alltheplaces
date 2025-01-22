from locations.storefinders.yext import YextSpider


class LushSpider(YextSpider):
    name = "lush"
    item_attributes = {"brand": "Lush", "brand_wikidata": "Q1585448"}

    api_key = "4f2cd9fa908385f9651911bbf9d6b2ff"
