from locations.storefinders.yext import YextSpider


class RecipeUnlimitedSpider(YextSpider):
    name = "recipe_unlimited"
    api_key = "13a5875d18fe490377fc4bf35de52851"
    wanted_types = ["restaurant"]

    brands = {
        "Añejo Restaurant": {
            "brand": "Añejo Restaurant",
            "brand_wikidata": "Q118744458",
            "extras": {"amenity": "restaurant", "cuisine": "mexican"},
        },
        "Blanco Cantina": {
            "brand": "Blanco Cantina",
            "brand_wikidata": "Q118744486",
            "extras": {"amenity": "restaurant", "cuisine": "mexican"},
        },
        "Bier Markt": {"brand": "Bier Markt", "brand_wikidata": "Q118744348", "extras": {"amenity": "biergarten"}},
        "East Side Mario's": {"brand": "East Side Mario's", "brand_wikidata": "Q5329375"},
        "Elephant & Castle": {
            "brand": "Elephant & Castle",
            "brand_wikidata": "Q118744342",
            "extras": {"amenity": "pub"},
        },
        "Express St-Hubert": {
            "brand": "St-Hubert Express",
            "brand_wikidata": "Q3495225",
            "extras": {"amenity": "restaurant", "cuisine": "chicken;barbecue"},
        },
        "Fresh Kitchen + Juice Bar": {
            "brand": "Fresh Kitchen + Juice Bar",
            "brand_wikidata": "Q118744242",
            "extras": {"amenity": "restaurant", "diet:vegetarian": "only"},
        },
        "Harvey's": {"brand": "Harvey's", "brand_wikidata": "Q1466184"},
        "Kelseys Original Roadhouse": {"brand": "Kelseys Original Roadhouse", "brand_wikidata": "Q6386459"},
        "Landing": {
            "brand": "The Landing Group",
            "brand_wikidata": "Q118744373",
            "extras": {"amenity": "restaurant", "cuisine": "american"},
        },
        "Montana": {"brand": "Montana's", "brand_wikidata": "Q17022490"},
        "New York Fries": {"brand": "New York Fries", "brand_wikidata": "Q7013558"},
        "Original Joe's": {"brand": "Original Joe's", "brand_wikidata": "Q118744382"},
        "Pickle Barrel": {
            "brand": "Pickle Barrel",
            "brand_wikidata": "Q7190888",
            "extras": {"amenity": "restaurant", "cuisine": "fusion"},
        },
        "State & Main": {"brand": "State & Main", "brand_wikidata": "Q118744509"},
        "St-Hubert": {
            "brand": "St-Hubert",
            "brand_wikidata": "Q3495225",
            "extras": {"amenity": "restaurant", "cuisine": "chicken;barbecue"},
        },
        "Swiss Chalet": {"brand": "Swiss Chalet", "brand_wikidata": "Q2372909"},
        "The Burger's Priest": {"brand": "The Burger's Priest", "brand_wikidata": "Q100255453"},
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
