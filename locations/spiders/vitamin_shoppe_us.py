from locations.storefinders.rio_seo import RioSeoSpider


class VitaminShoppeUSSpider(RioSeoSpider):
    name = "vitamin_shoppe_us"
    item_attributes = {"brand": "The Vitamin Shoppe", "brand_wikidata": "Q7772938"}
    end_point = "https://maps.locations.vitaminshoppe.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = location["location_display_name"].strip()
        yield feature
