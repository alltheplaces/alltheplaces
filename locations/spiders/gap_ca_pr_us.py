from locations.categories import Categories, Clothes, apply_clothes
from locations.storefinders.rio_seo import RioSeoSpider


class GapCAPRUSSpider(RioSeoSpider):
    name = "gap_ca_pr_us"
    item_attributes = {"brand": "Gap", "brand_wikidata": "Q420822", "extras": Categories.SHOP_CLOTHES.value}
    end_point = "https://www.gap.com/stores/maps"

    def post_process_feature(self, item, location):
        item["branch"] = item.pop("name")

        types = location["store_type"]
        if types == "Gap Factory Store":
            item["name"] = "Gap Factory"
        else:
            item["name"] = "Gap"
            if "GapBody" in types:
                apply_clothes([Clothes.UNDERWEAR], item)
            if "GapMaternity" in types:
                apply_clothes([Clothes.MATERNITY], item)
            if "babyGap" in types:
                apply_clothes([Clothes.BABY], item)
            if "GapKids" in types:
                apply_clothes([Clothes.CHILDREN], item)
        yield item
