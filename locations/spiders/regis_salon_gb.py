from locations.storefinders.uberall import UberallSpider


class RegisSalonsGBSpider(UberallSpider):
    name = "regis_salons_gb"
    item_attributes = {
        "brand_wikidata": "Q110166032",
        "brand": "Regis Salons",
    }
    key = "616eo7rrGeXiZ0jL1wrJ2JAlyx5RxR"