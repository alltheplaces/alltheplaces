import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TruistUSSpider(SitemapSpider, StructuredDataSpider):
    name = "truist_us"
    item_attributes = {
        "brand": "Truist",
        "brand_wikidata": "Q795486",
    }
    sitemap_urls = [
        "https://www.truist.com/branch.index.xml",
        "https://www.truist.com/atm.index.xml",
    ]
    sitemap_rules = [
        (r"^https://www.truist.com/\w+/[a-z]{2}/[\w-]+/\d+/[\w-]+$", "parse"),
    ]
    wanted_types = ["FinancialService", "AutomatedTeller"]
    search_for_twitter = False
    drop_attributes = {"facebook"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Name is formatted something like:
        # "Truist Somewhere Branch in City, XY, 00000"
        # or
        # "Truist Somewhere ATM in City, XY, 00000"
        branch = item.pop("name").removeprefix("Truist ")
        i = branch.find(" Branch")
        if i == -1:
            i = branch.find(" ATM")
        if i != -1:
            branch = branch[:i]
        item["branch"] = branch

        location_info = json.loads(response.xpath("//@data-location-info").get())
        item["ref"] = location_info.get("locationKey")
        if location_info.get("locationType").upper() == "BRANCH":
            if atm_detail := location_info.get("atmDetail"):
                atm = item.deepcopy()
                atm["ref"] = atm_detail[0].get("atmId")
                atm["phone"] = None
                atm["opening_hours"] = "24/7"
                apply_category(Categories.ATM, atm)
                yield atm
            apply_category(Categories.BANK, item)
        elif location_info.get("locationType").upper() == "ATM":
            apply_category(Categories.ATM, item)

        if ld_data["openingHours"] == "24 Hours":
            item["opening_hours"] = "24/7"
        else:
            oh = OpeningHours()
            for line in ld_data["openingHours"].split(", "):
                # Website implies PM of ending time, but OpeningHours assumes AM, so need to make explicit
                if line[-1].isdigit():
                    line += "PM"
                oh.add_ranges_from_string(line)
            item["opening_hours"] = oh

        item["extras"]["fax"] = location_info.get("fax")
        yield item

    def extract_amenity_features(self, item, response, ld_item):
        apply_yes_no(
            Extras.DRIVE_THROUGH,
            item,
            any(feature["name"] in ("Drive-up Window", "Drive Up") for feature in ld_item.get("amenityFeature", [])),
        )
        apply_yes_no(
            Extras.WHEELCHAIR,
            item,
            any(feature["name"] == "Handicapped Accessible" for feature in ld_item.get("amenityFeature", [])),
        )
