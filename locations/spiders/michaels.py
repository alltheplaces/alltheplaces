from locations.hours import OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class MichaelsSpider(Where2GetItSpider):
    name = "michaels"
    item_attributes = {"brand": "Michaels", "brand_wikidata": "Q6835667"}
    api_brand_name = "michaelsca"
    api_key = "288FB6BC-71EE-11E1-AA2E-C7DA57283E85"

    def parse_item(self, item, location):
        item["state"] = location["state"]
        if item["country"] == "US":
            item["website"] = (
                "https://locations.michaels.com/"
                + item["state"].lower()
                + "/"
                + item["city"].lower().replace(" ", "-")
                + "/"
                + item["ref"]
            )
        item["opening_hours"] = OpeningHours()
        if location.get("mon_sat") and location.get("mon_sat").upper() != "CLOSED":
            item["opening_hours"].add_days_range(
                ["Mo", "Tu", "We", "Th", "Fr", "Sa"],
                location.get("mon_sat").split(" - ", 1)[0],
                location.get("mon_sat").split(" - ", 1)[1],
                "%I:%M%p",
            )
        if location.get("sun") and location.get("sun").upper() != "CLOSED":
            item["opening_hours"].add_range(
                "Su", location.get("sun").split(" - ", 1)[0], location.get("sun").split(" - ", 1)[1], "%I:%M%p"
            )
        yield item
