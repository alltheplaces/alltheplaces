from locations.categories import Categories, apply_category
from locations.storefinders.yext import YextSpider


class BuildersFirstsourceUSSpider(YextSpider):
    name = "builders_firstsource_us"
    item_attributes = {"brand": "Builders FirstSource", "brand_wikidata": "Q27686100"}
    api_key = "75d03100e13baa02575a046100dc4a15"

    def parse_item(self, item, location):
        if "c_locationStoreName" in location:
            item["name"] = location["c_locationStoreName"]
        if "c_websiteLocationName" in location:
            item["website"] = (
                "https://www.bldr.com/location/"
                + location["c_websiteLocationName"].lower().replace(" ", "-")
                + "/"
                + location["meta"]["id"]
            )
        elif "c_locationStoreName" in location:
            item["website"] = (
                "https://www.bldr.com/location/"
                + location["c_locationStoreName"].lower().replace(" ", "-")
                + "/"
                + location["meta"]["id"]
            )
        item.pop("twitter")
        item["extras"].pop("contact:instagram")
        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
