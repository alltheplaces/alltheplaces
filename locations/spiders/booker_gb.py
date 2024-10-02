from locations.storefinders.yext_answers import YextAnswersSpider

brands = {
    "Booker": {"brand": "Booker", "brand_wikidata": "Q4943180"},
    "Makro": {"brand": "Makro", "brand_wikidata": "Q704606"},
}


class BookerGBSpider(YextAnswersSpider):
    name = "booker_gb"
    item_attributes = {"brand": "Booker", "brand_wikidata": "Q4943180"}
    api_key = "9ca92999bf86e368065b5018e3f82c74"
    experience_key = "yext-pages-locator-search"

    def parse_item(self, location, item):
        for brand_key in brands.keys():
            if brand_key in item["name"]:
                item.update(brands[brand_key])
        slug = location["data"]["slug"]
        item["website"] = f"https://www.booker.co.uk/branch-locator/{slug}"
        yield item
