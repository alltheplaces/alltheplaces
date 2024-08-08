from locations.categories import Categories
from locations.storefinders.yext_answers import YextAnswersSpider


class LaneBryantUSSpider(YextAnswersSpider):
    name = "lane_bryant_us"
    item_attributes = {"brand": "Lane Bryant", "brand_wikidata": "Q6485350", "extras": Categories.SHOP_CLOTHES.value}
    api_key = "ccfe136898dfe236489c4f9fb0b91ded"
    experience_key = "lane-bryant-locator"
