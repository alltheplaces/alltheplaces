import json

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class BigWAUSpider(Spider):
    name = "big_w_au"
    item_attributes = {"brand": "Big W", "brand_wikidata": "Q4906646"}
    allowed_domains = ["www.bigw.com.au"]
    # Any store URL page contains a full JSON blob of store data for all stores.
    start_urls = ["https://www.bigw.com.au/store/0145/BIG-W-Warringah-Mall"]
    # An alltheplaces user agent gets delayed in the hope of causing bots to time out
    # whereas a user agent having the appearance of a user is not delayed.
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        stores = json.loads(data_raw)["props"]["pageProps"]["serializedData"]["store"]
        for store in stores:
            properties = {
                "ref": store["id"],
                "name": store["n"],
                "phone": store["ph"],
                "street_address": store["a"]["street"],
                "city": store["a"]["suburb"],
                "state": store["a"]["state"],
                "postcode": store["a"]["postcode"],
                "lat": store["l"]["lat"],
                "lon": store["l"]["lng"],
            }
            properties["opening_hours"] = OpeningHours()
            hours_string = " ".join([f"{day} {hours}" for day, hours in store["hr"][0]["hours"].items()])
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
