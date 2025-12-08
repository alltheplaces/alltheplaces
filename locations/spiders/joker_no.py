from locations.storefinders.sylinder import SylinderSpider


class JokerNOSpider(SylinderSpider):
    name = "joker_no"
    item_attributes = {"brand": "Joker", "brand_wikidata": "Q716328"}
    app_key = "1220"
    base_url = "https://joker.no/finn-butikk"
