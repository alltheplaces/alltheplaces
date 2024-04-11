from locations.storefinders.sylinder import SylinderSpider


class KiwiNoSpider(SylinderSpider):
    name = "kiwi_no"
    item_attributes = {"brand": "Kiwi", "brand_wikidata": "Q1613639"}
    app_key = "1100"
    base_url = "https://kiwi.no/Finn-butikk/"
