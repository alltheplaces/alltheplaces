from locations.storefinders.elfsight import ElfsightSpider


class AnimaxROSpider(ElfsightSpider):
    name = "animax_ro"
    item_attributes = {"brand": "Animax", "brand_wikidata": "Q119440709"}
    host = "shy.elfsight.com"
    shop = "animaxro.myshopify.com"
    api_key = "73d5edfc-9672-4567-b102-02ef8265ef7e"
