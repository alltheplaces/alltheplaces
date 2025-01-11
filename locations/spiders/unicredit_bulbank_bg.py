from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class UnicreditBulbankBGSpider(JSONBlobSpider):
    name = "unicredit_bulbank_bg"
    item_attributes = {"brand": "UniCredit Bulbank", "brand_wikidata": "Q7884635"}
    start_urls = [
        "https://www.unicreditbulbank.bg/bg/api/locations/branches.json",
        "https://www.unicreditbulbank.bg/bg/api/locations/atms.json",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT
    locations_key = "data"

    def post_process_item(self, item, response, location):
        if "atms.json" in response.url:
            item["ref"] = f"atm-{item['ref']}"
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        if workhours := location.get("workhours"):
            item["opening_hours"] = oh = OpeningHours()
            for k, v in workhours.items():
                r = v.split(" - ")
                oh.add_range(DAYS_EN[k.title()], r[0], r[1])
        item["street_address"] = item.pop("addr_full", None)
        yield item
