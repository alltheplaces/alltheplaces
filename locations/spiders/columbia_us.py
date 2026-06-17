from locations.storefinders.yext_answers import YextAnswersSpider


class ColumbiaUSSpider(YextAnswersSpider):
    name = "columbia_us"
    item_attributes = {"brand": "Columbia", "brand_wikidata": "Q1112588"}
    api_key = "3e0457d17939280a4ed5eef2e99daf8b"
    experience_key = "pages-locator"
    facet_filters = {
        "$or": [
            {"c_storeType": {"$eq": "Brand Store"}},
            {"c_storeType": {"$eq": "Factory Store"}},
            {"c_storeType": {"$eq": "Clearance Store"}},
        ]
    }
