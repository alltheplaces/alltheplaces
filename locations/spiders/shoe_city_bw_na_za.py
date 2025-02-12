from locations.hours import OpeningHours
from locations.storefinders.amai_promap import AmaiPromapSpider


class ShoeCityBWNAZASpider(AmaiPromapSpider):
    name = "shoe_city_bw_na_za"
    start_urls = ["https://www.shoecity.co.za/pages/sca-store-locator"]
    item_attributes = {"brand": "Shoe City", "brand_wikidata": "Q116620945"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item.pop("email")
        if description := feature.get("description"):
            item["opening_hours"] = OpeningHours()
            for day in description.split("<br>"):
                item["opening_hours"].add_ranges_from_string(day)
        yield item
