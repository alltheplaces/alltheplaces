import secrets
import string

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BunningsSpider(scrapy.Spider):
    name = "bunnings"
    allowed_domains = ["bunnings.com.au"]
    start_urls = [
        "https://api.prod.bunnings.com.au/v1/stores?latitude=-23.12&longitude=132.13&currentPage=0&fields=FULL&pageSize=10000&radius=9000000",
    ]
    item_attributes = {"brand": "Bunnings", "brand_wikidata": "Q4997829"}
    custom_settings = {
        "COOKIES_ENABLED": True,
    }
    client_id = "mHPVWnzuBkrW7rmt56XGwKkb5Gp9BJMk"  # Fixed value of APIGEE_CLIENT_ID variable from store locator page.
    auth_token = ""

    def start_requests(self):
        nonce = "".join(secrets.choice(string.ascii_letters + string.digits) for i in range(18))
        yield scrapy.Request(
            f"https://authorisation.api.bunnings.com.au/connect/authorize?response_type=token&scope=chk:exec cm:access ecom:access chk:pub &client_id=budp_guest_user_au&redirect_uri=https://www.bunnings.com.au/static/guest.html&nonce={nonce}&acr_values=",
            self.parse_guest_login_page,
        )

    def parse_guest_login_page(self, response):
        self.auth_token = response.request.url.split("#access_token=", 1)[1].split("&token_type=", 1)[0]
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                self.parse,
                headers={
                    "Authorization": "Bearer " + self.auth_token,
                    "clientId": self.client_id,
                    "country": "AU",
                    "locale": "en_AU",
                },
            )

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
                if not day["closed"]:
                    oh.add_range(
                        day=day["weekDay"],
                        open_time=day["openingTime"]["formattedHour"],
                        close_time=day["closingTime"]["formattedHour"],
                        time_format="%I:%M %p",
                    )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
