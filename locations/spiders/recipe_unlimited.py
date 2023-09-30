from locations.storefinders.yext import YextSpider


class RecipeUnlimitedSpider(YextSpider):
    name = "recipe_unlimited"
    api_key = "13a5875d18fe490377fc4bf35de52851"
    wanted_types = ["restaurant"]

    brands = {
        "Añejo Restaurant": {"brand": "Añejo Restaurant", "brand_wikidata": "Q118744458"},
        "Blanco Cantina": {"brand": "Blanco Cantina", "brand_wikidata": "Q118744486"},
        "Bier Markt": {"brand": "Bier Markt", "brand_wikidata": "Q118744348"},
        "East Side Mario's": {"brand": "East Side Mario's", "brand_wikidata": "Q5329375"},
        "Elephant & Castle": {"brand": "Elephant & Castle", "brand_wikidata": "Q118744342"},
        "Express St-Hubert": {"brand": "St-Hubert Express", "brand_wikidata": "Q3495225"},
        "Fresh Kitchen + Juice Bar": {"brand": "Fresh Kitchen + Juice Bar", "brand_wikidata": "Q118744242"},
        "Harvey's": {"brand": "Harvey's", "brand_wikidata": "Q1466184"},
        "Kelseys Original Roadhouse": {"brand": "Kelseys Original Roadhouse", "brand_wikidata": "Q6386459"},
        "Landing": {"brand": "The Landing Group", "brand_wikidata": "Q118744373"},
        "Montana's": {"brand": "Montana's", "brand_wikidata": "Q17022490"},
        "New York Fries": {"brand": "New York Fries", "brand_wikidata": "Q7013558"},
        "Original Joe's": {"brand": "Original Joe's", "brand_wikidata": "Q118744382"},
        "Pickle Barrel": {"brand": "Pickle Barrel", "brand_wikidata": "Q7190888"},
        "State & Main": {"brand": "State & Main", "brand_wikidata": "Q118744509"},
        "St-Hubert": {"brand": "St-Hubert", "brand_wikidata": "Q3495225"},
        "Swiss Chalet": {"brand": "Swiss Chalet", "brand_wikidata": "Q2372909"},
        "The Burger's Priest": {"brand": "The Burger's Priest", "brand_wikidata": "Q100255453"},
        "Ultimate Kitchens": {"brand": "Ultimate Kitchens", "brand_wikidata": "Q118744353"},
    }

    def parse_item(self, item, location):
        store_name = None
        if location.get("c_storeName"):
            store_name = location["c_storeName"]
        else:
            store_name = item["name"]

        if "1909 Taverne Moderne" in store_name or "Recipe Unlimited" in store_name:
            # These brands are either defunct or not legitimate
            # and do not have a 'closed' field to filter on.
            return

        for brand_key in self.brands.keys():
            if brand_key in store_name:
                item.update(self.brands[brand_key])
                break

        # Twitter handles, Instagram handles and websites are not
        # restaurant-specific.
        item.pop("website")
        item.pop("twitter")
        if "contact:instagram" in item["extras"].keys():
            item["extras"].pop("contact:instagram")

        yield item
