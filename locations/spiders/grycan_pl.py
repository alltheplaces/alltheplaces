from locations.hours import DAYS_PL, OpeningHours
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class GrycanPLSpider(WpGoMapsSpider):
    name = "grycan_pl"
    item_attributes = {"brand": "Grycan", "brand_wikidata": "Q97372889"}
    allowed_domains = ["grycan.pl"]

    def post_process_item(self, item, location):
        custom_field_data = location["custom_field_data"]

        if custom_field_data == []:
            return item

        if "Telefon" in custom_field_data.keys():
            item["phone"] = custom_field_data["Telefon"]

        if "Kod pocztowy" in custom_field_data.keys():
            item["postcode"] = custom_field_data["Kod pocztowy"]

        if "Ulica" in custom_field_data.keys():
            item["street"] = custom_field_data["Ulica"]

        if "Miasto" in custom_field_data.keys():
            item["city"] = custom_field_data["Miasto"]

        if "Województwo" in custom_field_data.keys():
            item["state"] = custom_field_data["Województwo"]

        item["opening_hours"] = OpeningHours()

        for key in custom_field_data.keys():
            if "Godziny otwarcia w" in key:
                # Godziny otwarcia we Wtorek or Godziny otwarcia w Poniedziałek
                day_name = key.split(" ")[3]
                if " | " in custom_field_data[key]:
                    opens, closes = custom_field_data[key].split(" | ")
                    item["opening_hours"].add_range(DAYS_PL[day_name], opens, closes, "%H:%M:%S")
                elif "-" in custom_field_data[key]:  # 10-21
                    opens, closes = custom_field_data[key].split("-")
                    item["opening_hours"].add_range(DAYS_PL[day_name], opens, closes, "%H")

        return item
