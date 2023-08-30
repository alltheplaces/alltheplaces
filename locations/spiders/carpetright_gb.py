from locations.storefinders.yext import YextSpider


class CarpetrightGBSpider(YextSpider):
    name = "carpetright_gb"
    item_attributes = {"brand": "carpetright", "brand_wikidata": "Q5045782"}
    api_key = "a3853af22833fc3224b846180ad0bcc0"
