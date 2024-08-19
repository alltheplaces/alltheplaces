from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo import RioSeoSpider


class SaversCAUSSpider(RioSeoSpider):
    name = "savers_ca_us"
    item_attributes = {
        "brand": "Savers",
        "name": "Savers",
        "brand_wikidata": "Q7428188",
    }
    end_point = "https://maps.savers.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")

        if feature["branch"].startswith("Community Donation Cent"):
            feature["branch"] = feature["branch"].removeprefix("Community Donation Center - ")
            feature["branch"] = feature["branch"].removeprefix("Community Donation Centre - ")
            apply_category({"amenity": "recycling", "recycling_type": "centre"}, feature)
        else:
            apply_category(Categories.SHOP_SECOND_HAND, feature)

        if location["Brands_CS"] == "Value Village":
            feature["brand"] = feature["name"] = "Value Village"

        if location["openingDate"].count("/") == 2:
            m, d, y = map(int, location["openingDate"].split("/"))
            feature["extras"]["start_date"] = f"{y}.{m:02}.{d:02}"

        yield feature
