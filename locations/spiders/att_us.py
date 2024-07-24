import re

from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.where2getit import Where2GetItSpider
from locations.structured_data_spider import clean_facebook


class AttUSSpider(Where2GetItSpider):
    name = "att_us"
    item_attributes = {"brand": "AT&T", "brand_wikidata": "Q298594"}
    api_endpoint = "https://www.att.com/stores/rest/getlist"
    api_key = "2F8B3130-66C5-11ED-9608-26F2C42605F6"
    api_filter_admin_level = 2

    def parse_item(self, item, location):
        if not location.get("company_owned_stores"):
            return
        item["ref"] = location["clientkey"]
        item["name"] = re.sub(r" - \d+$", "", item["name"])
        if location.get("address1") == "123 Main Street":
            item.pop("street_address", None)
        else:
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
        item["facebook"] = clean_facebook(location.get("facebook_url"))
        if location.get("bho") and len(location.get("bho")) == 7:
            item["opening_hours"] = OpeningHours()
            for index, day in enumerate(DAYS_3_LETTERS_FROM_SUNDAY):
                if location["bho"][index][0] == "9999" or location["bho"][index][1] == "9999":
                    continue
                item["opening_hours"].add_range(day, location["bho"][index][0], location["bho"][index][1], "%H%M")
        yield item
