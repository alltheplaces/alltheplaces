from locations.storefinders.closeby import ClosebySpider


class PatisserieValerieGBSpider(ClosebySpider):
    name = "patisserie_valerie_gb"
    item_attributes = {
        "brand_wikidata": "Q22101966",
        "brand": "Patisserie Valerie",
    }
    api_key = "f312dbbc1e1036a6e7b395fbd18aaf1f"
