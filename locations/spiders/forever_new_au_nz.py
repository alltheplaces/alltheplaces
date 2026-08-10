import json

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT

FOREVER_NEW_SHARED_ATTRIBUTES = {"brand": "Forever New", "brand_wikidata": "Q119221929"}


class ForeverNewAUNZSpider(JSONBlobSpider, PlaywrightSpider):
    name = "forever_new_au_nz"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.forevernew.com.au/locator/index/search/?address=sydney&components[country]=AU&radius=1000000000&type=all",
        "https://www.forevernew.co.nz/locator/index/search/?address=wellington&components[country]=NZ&radius=1000000000&type=all",
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True

    def extract_json(self, response: TextResponse):
        data = json.loads(response.xpath("//pre/text()").get())["results"]["results"]
        return data

    def post_process_item(self, item, response, location):
        # Ignore locations which are embedded within a Myer department store.
        if location.get("name") is not None and " MYER " in location["name"].upper():
            return
        hours = json.loads(location["trading_hours"])
        item["branch"] = item.pop("name").replace("Forever New - ", "")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(str(hours))
        yield item
