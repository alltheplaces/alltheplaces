from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.rio_seo import RioSeoSpider


class PeoplesBankUSSpider(RioSeoSpider):
    name = "peoples_bank_us"
    item_attributes = {"brand": "Peoples Bank", "brand_wikidata": "Q65716607"}
    end_point = "https://maps.locations.peoplesbancorp.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")

        location_type = location["Location Type_CS"]
        if location_type == "Branch & ATM":
            apply_category(Categories.BANK, feature)
            apply_yes_no(Extras.ATM, feature, True)
            feature["name"] = self.item_attributes["brand"]
        elif location_type == "Branch":
            apply_category(Categories.BANK, feature)
            feature["name"] = self.item_attributes["brand"]
        elif location_type == "24 hour ATM":
            apply_category(Categories.ATM, feature)
            feature["operator"] = self.item_attributes["brand"]
            feature["operator_wikidata"] = self.item_attributes["brand_wikidata"]
        elif location_type == "Insurance Location":
            apply_category(Categories.OFFICE_INSURANCE, feature)
            feature["name"] = self.item_attributes["brand"]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_type/{location_type}")
            apply_category(Categories.BANK, feature)
            feature["name"] = self.item_attributes["brand"]

        oh = self.parse_hours(location["hours_sets:drive_thru_hours"])
        if oh is not None:
            feature["extras"]["opening_hours:drive_through"] = oh.as_opening_hours()
        oh = self.parse_hours(location["hours_sets:atm_hours"])
        if oh is not None:
            feature["extras"]["opening_hours:atm"] = oh.as_opening_hours()

        yield feature
