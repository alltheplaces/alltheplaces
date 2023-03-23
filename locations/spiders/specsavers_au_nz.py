from locations.storefinders.yext import YextSpider


class SpecsaversAUNZSpider(YextSpider):
    name = "specsavers_au_nz"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    api_key = "be3071a8d4114a2731d389952dd3eeb2"
