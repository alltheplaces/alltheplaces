from locations.storefinders.amrest_eu import AmrestEUSpider


class LaTagliatellaESSpider(AmrestEUSpider):
    name = "la_tagliatella_es"
    base_urls = ["https://api.amrest.eu/amdv/ordering-api/TAG_ES/"]  # https://www.latagliatella.es/restaurantes
    item_attributes = {
        "brand": "La Tagliatella",
        "brand_wikidata": "Q113426257",
    }

    def parse_item(self, item, feature, **kwargs):
        # storeLocatorUrl format vary for other Amrest brands
        item["website"] = feature.get("storeLocatorUrl")
        item["branch"] = item.pop("name")
        yield item
