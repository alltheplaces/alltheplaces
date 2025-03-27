from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.json_blob_spider import JSONBlobSpider


class TdBankSpider(JSONBlobSpider):
    name = "td_bank"
    item_attributes = {
        "brand": "TD Bank",
        "brand_wikidata": "Q7669891",
    }
    start_urls = [
        "https://www.tdbank.com/net/get12.ashx?longitude=-94&latitude=48&json=y&searchradius=25000&searchunit=mi&numresults=10000"
    ]
    locations_key = ["markers", "marker"]

    def post_process_item(self, item, response, location):
        item.pop("name", None)
        item["country"] = location["coun"].upper()
        item["extras"]["fax"] = location.get("faxno")
        item["extras"]["start_date"] = location.get("opendate")

        apply_yes_no(Extras.DRIVE_THROUGH, item, location["driveup"] == "Y", location["driveup"] != "N")
        apply_yes_no(Extras.WHEELCHAIR, item, location["wheelchair"] == "Y", location["wheelchair"] != "N")

        if location["type"] == "1":
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, location["type"] == "3")
        if location["coun"] == "ca":
            item["brand"] = "TD"
            item["brand_wikidata"] = "Q1080670"
        if item.get("isshutdown") == "Y":
            set_closed(item)

        if branch_n := location["branchN"]:
            item["website"] = f"https://locations.td.com/{branch_n}"

        if currencies := location["currencies"]:
            for currency in currencies.split(", "):
                apply_yes_no(f"currency:{currency.upper()}", item, True)
        if languages := location["languages"]:
            for language in languages.split("|"):
                apply_yes_no(f"language:{language}", item, True)

        if (location["driveup"] == "Y") and (driveuphours := location.get("driveuphours")):
            item["extras"]["opening_hours:drive_through"] = self.parse_hours(driveuphours).as_opening_hours()
        if hours := location.get("hours"):
            item["opening_hours"] = self.parse_hours(hours)

        yield item

    def parse_hours(self, hours):
        oh = OpeningHours()
        for day, times in hours.items():
            if times == "CLOSED":
                oh.set_closed(day)
            else:
                opening, closing = times.split(" - ")
                oh.add_range(day, opening, closing, time_format="%I:%M %p")
        return oh
