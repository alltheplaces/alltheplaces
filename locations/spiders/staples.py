from locations.storefinders.yext import YextSpider


class StaplesSpider(YextSpider):
    name = "staples"
    item_attributes = {"brand": "Staples", "brand_wikidata": "Q785943"}
    api_key = "a05b56686f7bf3558831122f8a32e69f"
    api_version = "20220927"
