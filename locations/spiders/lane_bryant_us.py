from locations.storefinders.yext import YextSpider


class LaneBryantUSSpider(YextSpider):
    name = "lane_bryant_us"
    item_attributes = {"brand": "Lane Bryant", "brand_wikidata": "Q6485350"}
    api_key = "ccfe136898dfe236489c4f9fb0b91ded"
    api_version = "20220511"
