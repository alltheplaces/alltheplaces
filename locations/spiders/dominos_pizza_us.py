from locations.storefinders.yext_answers import YextAnswersSpider


class DominosPizzaUSSpider(YextAnswersSpider):
    name = "dominos_pizza_us"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    experience_key = "locator"
    api_key = "db579cbf33dcf239cfae2d4466f5ce59"

    def parse_item(self, location, item):
        item["website"] = location["c_pagesURL"]
        if item["website"] == "https://pizza.dominos.com/new-york/new-york/61-ninth-avenue":
            return  # "Test Location"

        item["extras"].pop("website:menu", None)

        yield item
