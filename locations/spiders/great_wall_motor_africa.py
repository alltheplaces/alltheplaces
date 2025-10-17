from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.great_wall_motor_au_nz import GREAT_WALL_MOTOR_SHARED_ATTRIBBUTES


class GreatWallMotorAfricaSpider(JSONBlobSpider):
    name = "great_wall_motor_africa"
    item_attributes = GREAT_WALL_MOTOR_SHARED_ATTRIBBUTES
    start_urls = ["https://www.gwm.co.za/graphql/execute.json/gwm/za-dealer-list"]
    locations_key = ["data", "zaDealerList", "items"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["addr_full"] = location["detailAddress"]
        try:
            int(item["addr_full"].split(",")[-1])
            item["postcode"] = item["addr_full"].split(",")[-1]
            item["city"] = item["addr_full"].split(",")[-2]
        except:
            pass
        if item["state"] in [
            "Botswana",
            "Eswatini",
            "Kenya",
            "Lesotho",
            "Malawi",
            "Mauritius",
            "Mozambique",
            "Namibia",
            "Seychelles",
            "Zambia",
            "Zimbabwe",
        ]:
            item.pop("state")

        item["phone"] = location.get("serviceHotline")

        apply_category(Categories.SHOP_CAR, item)

        yield item
