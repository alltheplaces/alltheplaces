from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class MarionnaudSpider(JSONBlobSpider):
    name = "marionnaud"
    item_attributes = {"brand": "Marionnaud", "brand_wikidata": "Q1129073"}
    start_urls = [
        "https://api.marionnaud.at/api/v2/mat/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.ch/api/v2/mch/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.cz/api/v2/mcz/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.hu/api/v2/mhu/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.it/api/v2/mit/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.ro/api/v2/mro/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.sk/api/v2/msk/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://api.marionnaud.fr/api/v2/mfr/stores?radius=10000&pageSize=100000&fields=FULL",
    ]
    locations_key = "stores"
    user_agent = BROWSER_DEFAULT
    requires_proxy = True
    needs_json_request = True

    def pre_process_data(self, location):
        location.update(location.pop("address"))

    def post_process_item(self, item, response, location):
        item["addr_full"] = location["formattedAddress"]
        item["street_address"] = merge_address_lines([location["line1"], location.get("line2")])
        item["website"] = response.urljoin(location["url"]).replace("api.marionnaud", "www.marionnaud")

        item["opening_hours"] = OpeningHours()
        for rule in location["openingHours"]["weekDayOpeningList"]:
            if rule["closed"]:
                item["opening_hours"].set_closed(rule["shortenedWeekDay"])
                continue
            item["opening_hours"].add_range(
                rule["shortenedWeekDay"],
                rule["openingTime"]["formattedHour"].replace(".", ":"),
                rule["closingTime"]["formattedHour"].replace(".", ":"),
            )
        yield item
