from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class PonderosaBonanzaSteakhouseUSSpider(StoreRocketSpider):
    name = "ponderosa_bonanza_steakhouse_us"
    ponderosa = {"brand": "Ponderosa Steakhouse", "brand_wikidata": "Q64038204"}
    bonanza = {"brand": "Bonanza Steakhouse", "brand_wikidata": "Q64045992"}
    storerocket_id = "DB8ebGWp9M"
    base_url = "https://pon-bon.com/locations"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if location["location_type_name"] == "Ponderosa Steakhouse":
            item.update(self.ponderosa)
        elif location["location_type_name"] == "Bonanza Steakhouse":
            item["extras"]["branch"] = item.pop("name")
            item.update(self.bonanza)

        item["opening_hours"] = OpeningHours()
        for day, times in location["hours"].items():
            if times == "closed":
                continue
            item["opening_hours"].add_range(
                day, *times.replace(",", "-").replace("p", "pm").replace("a", "am").split("-"), "%I:%M%p"
            )

        yield item
