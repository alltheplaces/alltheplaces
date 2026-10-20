from locations.storefinders.yext_answers import YextAnswersSpider


class MarugameJPSpider(YextAnswersSpider):
    name = "marugame_jp"
    item_attributes = {"brand": "丸亀製麺", "brand_wikidata": "Q10877253"}
    api_key = "edab7c96fe6c7aadfe451c5b67bae16e"
    experience_key = "marugame-pages-locator"
    feature_type = "restaurants"
    locale = "ja"
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"

    def parse_item(self, location, item):
        item["name"] = None
        item["branch"] = location.get("geomodifier")
        item["website"] = f"https://stores.marugame.com/{location.get('slug')}"
        if menu_url := location.get("menuUrl"):
            item["extras"]["website:menu"] = menu_url.get("displayUrl")

        # Non-standard Yext fields were not mapped to OSM tags:
        #   c_availableFlags (e.g. ["小", "得"])  - menu size/promotion flags
        #   c_keieiKeitai ("直営" direct-operated) - ownership model, not on OSM
        #   c_eatinTakeoutList (eat-in / takeout menu categories)

        yield item
