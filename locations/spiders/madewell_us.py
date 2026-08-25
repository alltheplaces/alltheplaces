from locations.storefinders.yext import YextSpider


class MadewellUSSpider(YextSpider):
    name = "madewell_us"
    item_attributes = {"brand": "Madewell", "brand_wikidata": "Q64026213"}
    api_key = "c0963a72b0de0906e149ff1daac427d0"
    api_version = "20240514"
    search_filter = '{"$and":[{"c_storeChannel":{"$eqAny":["Madewell"]}},{"closed":{"$eq":false}}]}'
