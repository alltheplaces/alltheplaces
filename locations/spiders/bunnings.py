import json

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BunningsSpider(Spider):
    name = "bunnings"
    allowed_domains = ["bunnings.com.au"]
    start_urls = [
        "https://api.prod.bunnings.com.au/v1/stores?latitude=-23.12&longitude=132.13&currentPage=0&fields=FULL&pageSize=10000&radius=9000000",
    ]
    item_attributes = {"brand": "Bunnings", "brand_wikidata": "Q4997829"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    client_id = "mHPVWnzuBkrW7rmt56XGwKkb5Gp9BJMk"  # Fixed value of APIGEE_CLIENT_ID variable from store locator page.
    requires_proxy = "AU"  # Requires AU or NZ proxy, possibly residential IP addresses only.

    def start_requests(self):
        yield Request(url="https://www.bunnings.com.au/", callback=self.parse_cookies)

    def parse_cookies(self, response):
        cookies = response.headers.getlist("Set-Cookie")
        for cookie in cookies:
            if "guest-token-storage" not in str(cookie):
                continue
            token_dict = json.loads("{" + str(cookie).split("={", 1)[1].split("}", 1)[0] + "}")
            auth_token = token_dict["token"]
            headers = {
                "Authorization": "Bearer " + auth_token,
                "clientId": self.client_id,
                "country": "AU",
                "locale": "en_AU",
            }
            for url in self.start_urls:
                yield Request(url=url, headers=headers, callback=self.parse)
            return

    def parse(self, response):
        if response.json()["statusDetails"]["state"] != "SUCCESS":
            return
        for location in response.json()["data"]["stores"]:
            if not location["isActiveLocation"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["name"]
            item["name"] = location["displayName"]
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            if item["country"] == "NZ":
                item.pop("state")
                website_prefix = "https://www.bunnings.co.nz/stores/"
            else:
                item["state"] = location["address"]["region"]["isocode"]
                website_prefix = "https://www.bunnings.com.au/stores/"
            if "urlRegion" in location:
                item["website"] = website_prefix + location["urlRegion"] + "/" + item["name"].lower().replace(" ", "-")
            item["extras"]["website:map"] = location.get("mapUrl")
            oh = OpeningHours()
            for day in location["openingHours"]["weekDayOpeningList"]:
                if (
                    not day["closed"]
                    and day.get("openingTime")
                    and day["openingTime"].get("formattedHour")
                    and day.get("closingTime")
                    and day["closingTime"].get("formattedHour")
                ):
                    oh.add_range(
                        day=day["weekDay"],
                        open_time=day["openingTime"]["formattedHour"],
                        close_time=day["closingTime"]["formattedHour"],
                        time_format="%I:%M %p",
                    )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
