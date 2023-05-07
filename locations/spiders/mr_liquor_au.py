from locations.storefinders.metizsoft import MetizsoftSpider


class MrLiquorAUSpider(MetizsoftSpider):
    name = "mr_liquor_au"
    item_attributes = {"brand": "Mr Liquor", "brand_wikidata": "Q117822077"}
    shopify_url = "mr-liquor.myshopify.com"
