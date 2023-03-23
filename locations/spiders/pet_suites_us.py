from locations.storefinders.yext import YextSpider


class PetSuitesUSSpider(YextSpider):
    name = "pet_suites_us"
    item_attributes = {"brand": "PetSuites", "brand_wikidata": "Q112037454"}
    api_key = "a17dd90fe0e16548cdbf95de53725f70"
    api_version = "20161012"
    search_filter = '{"meta.folderId":{"$in":[249017]}}'
