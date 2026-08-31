from locations.categories import Categories, apply_category
from locations.storefinders.yext_answers import YextAnswersSpider

brands = {
    "ツルハ": {"brand": "ツルハドラッグ", "brand_wikidata": "Q11318826"},
    "福太郎": {"brand": "くすりの福太郎", "brand_wikidata": "Q17214460"},
    "杏林堂": {"brand": "杏林堂", "brand_wikidata": "Q11522605"},
    "イレブン": {"brand": "ドラッグイレブン", "brand_wikidata": "Q11323075"},
    "ウォンツ": {"brand": "ウォンツ"},  # no wikidata for below
    "ウェルネス": {"brand": "ウェルネス"},
    "レデイ": {"brand": "くすりのレデイ"},
    "B＆D": {"brand": "B＆D調剤薬局"},
}


class TsuruhadrugSpider(YextAnswersSpider):
    name = "tsuruhadrug"
    # item_attributes = {"brand": "ツルハドラッグ", "brand_wikidata": "Q11318826"}

    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    api_key = "6f3d5119d849cfdb44094409f825f542"
    experience_key = "shop-search"
    locale = "ja"

    def parse_item(self, location, item):
        if "c" in item["ref"]:
            item = None  # skip pharmacy ids
            return

        for brand_key in brands.keys():
            if brand_key in item["name"]:
                item.update(brands[brand_key])

        item["branch"] = (
            item.get("name")
            .removeprefix("ツルハドラッグ")
            .removeprefix("くすりの福太郎")
            .removeprefix("杏林堂")
            .removeprefix("ドラッグイレブン")
            .removeprefix("ウォンツ")
            .removeprefix("くすりのレデイ")
            .removeprefix("B＆D調剤薬局")
        )

        item["name"] = None

        apply_category(Categories.SHOP_CHEMIST, item)

        yield item
