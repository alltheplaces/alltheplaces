from locations.storefinders.sylinder import SylinderSpider


class MenyNOSpider(SylinderSpider):
    name = "meny_no"
    item_attributes = {"brand": "Meny", "brand_wikidata": "Q10581720"}
    app_key = "1300"
    base_url = "https://meny.no/finn-butikk/"
