from locations.spiders.central_england_cooperative import set_operator
from locations.storefinders.yext import YextSpider


class DreamsGBSpider(YextSpider):
    name = "dreams_gb"
    item_attributes = {"brand": "Dreams", "brand_wikidata": "Q5306688"}
    api_key = "653b917ffb5e9db1dc81b9756563b7c3"
    api_version = "20220927"

    def parse_item(self, item, location, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Dreams").strip(" -")
        if item["branch"].endswith(" - FRANCHISEE MAINTAINS"):
            item["branch"] = item["branch"].removesuffix(" - FRANCHISEE MAINTAINS")
        else:
            set_operator(self.item_attributes, item)

        item["website"] = item["website"].split("?", 1)[0]

        yield item
