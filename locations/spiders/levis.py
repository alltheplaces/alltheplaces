from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo import RioSeoSpider


class LevisSpider(RioSeoSpider):
    name = "levis"
    end_point = "https://maps.levi.com"

    def post_process_feature(self, item, location):
        apply_category(Categories.SHOP_CLOTHES, item)
        if item["name"].startswith("Dockers® "):
            item["brand"] = "Dockers"
            item["brand_wikidata"] = "Q538792"
        else:
            item["brand"] = "Levi's"
            item["brand_wikidata"] = "Q127962"

        item["branch"] = (
            item["name"].removeprefix(item["brand"]).removeprefix("® ").removeprefix("Factory ").removeprefix("Outlet ")
        )

        if location["Store Type_CS"] == "Levi's® Outlet":
            item["name"] = item["brand"] + " Outlet"
        else:
            item["name"] = item["brand"]

        yield item
