from locations.storefinders.freshop import FreshopSpider


class FestivalFoodsUSSpider(FreshopSpider):
    name = "festival_foods_us"
    item_attributes = {"brand": "Festival Foods", "brand_wikidata": "Q5445707"}
    app_key = "festival_foods_envano"

    def parse_item(self, item, location):
        if item.get("phone"):
            item["phone"] = item["phone"].replace("Guest Services: ", "").split("<br>", 1)[0].strip()
        if item.get("website"):
            item["website"] = "https://www.festfoods.com" + item["website"]
        yield item
