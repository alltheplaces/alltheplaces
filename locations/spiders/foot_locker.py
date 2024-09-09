from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.storefinders.rio_seo import RioSeoSpider


class FootLockerSpider(RioSeoSpider):
    name = "foot_locker"
    end_point = "https://maps.stores.footlocker.com"

    def post_process_feature(self, feature, location):
        if "Champs Sports" in feature["name"]:
            feature["brand"] = "Champs Sports"
            feature["brand_wikidata"] = "Q2955924"
            apply_category(Categories.SHOP_SPORTS, feature)

        elif feature["name"] == "Kids Foot Locker":
            feature["brand"] = "Kids Foot Locker"
            feature["brand_wikidata"] = "Q108100400"
            apply_category(Categories.SHOP_SHOES, feature)
            apply_clothes([Clothes.CHILDREN], feature)

        elif feature["name"] == "Lady Foot Locker":
            feature["brand"] = "Lady Foot Locker"
            feature["brand_wikidata"] = "Q108100505"
            apply_category(Categories.SHOP_SHOES, feature)
            apply_clothes([Clothes.WOMEN], feature)

        elif "Eastbay" in feature["name"]:
            feature["brand"] = "Eastbay"
            feature["brand_wikidata"] = "Q5329796"
            apply_category(Categories.SHOP_SHOES, feature)

        elif "House Of Hoops" in feature["name"].title():
            feature["brand"] = "House of Hoops"
            feature["brand_wikidata"] = "Q108232933"
            apply_category(Categories.SHOP_SHOES, feature)

        else:
            feature["brand"] = "Foot Locker"
            feature["brand_wikidata"] = "Q63335"
            apply_category(Categories.SHOP_SHOES, feature)

        yield feature
