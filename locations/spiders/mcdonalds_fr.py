from locations.categories import Extras, apply_yes_no
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.storefinders.woosmap import WoosmapSpider


class McdonaldsFRSpider(WoosmapSpider):
    name = "mcdonalds_fr"
    item_attributes = McdonaldsSpider.item_attributes
    key = "woos-77bec2e5-8f40-35ba-b483-67df0d5401be"
    origin = "https://www.mcdonalds.fr"

    def parse_item(self, item, feature, **kwargs):
        item["website"] = (
            f'https://www.mcdonalds.fr/restaurants{feature["properties"]["contact"]["website"]}/{feature["properties"]["store_id"]}'
        )
        item["postcode"] = feature["properties"]["user_properties"]["displayPostCode"]
        item["extras"]["check_date"] = feature["properties"]["last_updated"]
        item["branch"] = item.pop("name").title()

        apply_yes_no(Extras.DELIVERY, item, "mcdelivery" in feature["properties"]["tags"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "mcdrive" in feature["properties"]["tags"])
        apply_yes_no(Extras.INDOOR_SEATING, item, "table-service" in feature["properties"]["tags"])
        apply_yes_no(Extras.TAKEAWAY, item, "take-away" in feature["properties"]["tags"])
        apply_yes_no(Extras.SELF_CHECKOUT, item, "terminal" in feature["properties"]["tags"])
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "terrace" in feature["properties"]["tags"])
        apply_yes_no(Extras.WIFI, item, "wireless" in feature["properties"]["tags"])

        yield item
