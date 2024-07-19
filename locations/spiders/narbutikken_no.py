from locations.storefinders.sylinder import SylinderSpider


class NarbutikkenNOSpider(SylinderSpider):
    name = "narbutikken_no"
    item_attributes = {"brand": "Nærbutikken", "brand_wikidata": "Q108810007"}
    app_key = "1270"
    base_url = "https://narbutikken.no/Finn-butikk/"
