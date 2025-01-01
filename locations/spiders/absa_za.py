from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class AbsaZASpider(JSONBlobSpider):
    name = "absa_za"
    item_attributes = {"brand": "ABSA", "brand_wikidata": "Q58641733"}
    start_urls = ["https://www.absa.co.za/etc/barclays/contact-info/south-africa/_jcr_content/locations.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, location):
        if location["type"] == "branch":
            apply_category(Categories.BANK, item)
        elif location["type"] == "atm":
            apply_category(Categories.ATM, item)
        else:
            # there are a number of "dealer" types, ignore
            return

        item["street_address"] = clean_address(item["addr_full"])
        try:
            int(item["addr_full"].split(" ")[0])
            item["housenumber"] = item["addr_full"].split(" ")[0]
            item["street"] = item["addr_full"].split(",")[0].replace(item["housenumber"], "").strip()
        except ValueError:
            pass

        item["branch"] = item.pop("name")
        if "weekdayHours" in location and "weekendHours" in location:
            oh = OpeningHours()
            for times in location.get("weekdayHours").split(";"):
                oh.add_ranges_from_string("Mo-Fr " + times)
            for day_times in location.get("weekendHours").split(","):
                day, times = day_times.split(": ")
                if "closed" in times.lower():
                    oh.set_closed(day)
                else:
                    oh.add_ranges_from_string(day_times)
            item["opening_hours"] = oh.as_opening_hours()
        yield item
