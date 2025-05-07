import secrets
import string
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class BunningsSpider(Spider):
    name = "bunnings"
    allowed_domains = ["bunnings.com.au"]
    start_urls = [
        "https://api.prod.bunnings.com.au/v1/stores?latitude=-23.12&longitude=132.13&currentPage=0&fields=FULL&pageSize=10000&radius=9000000",
    ]
    item_attributes = {"brand": "Bunnings Warehouse", "brand_wikidata": "Q4997829"}
    custom_settings = {"COOKIES_ENABLED": True, "ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"  # Requires AU or NZ proxy, possibly residential IP addresses only.

    def start_requests(self) -> Iterable[Request]:
        yield Request(url="https://www.bunnings.com.au", callback=self.parse_apigee_client_id)

    def parse_apigee_client_id(self, response: Response) -> Iterable[Request]:
        apigee_client_id = response.text.split('"APIGEE_CLIENT_ID":"', 1)[1].split('"', 1)[0]
        nonce = "".join(secrets.choice(string.ascii_letters + string.digits) for i in range(18))
        yield Request(
            url=f"https://authorisation.api.bunnings.com.au/External/Challenge?provider=localloopback&returnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fresponse_type%3Dtoken%26scope%3Dchk%253Aexec%2520cm%253Aaccess%2520ecom%253Aaccess%2520chk%253Apub%2520vch%253Apublic%2520%26client_id%3Dbudp_guest_user_au%26redirect_uri%3Dhttps%253A%252F%252Fwww.bunnings.com.au%252Fstatic%252Fguest.html%26nonce%3D{nonce}%26acr_values%3D",
            meta={
                "dont_redirect": True,
                "handle_httpstatus_list": [302],
                "apigee_client_id": apigee_client_id,
                "nonce": nonce,
            },
            callback=self.parse_idsrv_cookie_1,
        )

    def parse_idsrv_cookie_1(self, response: Response) -> Iterable[Request]:
        apigee_client_id = response.meta["apigee_client_id"]
        nonce = response.meta["nonce"]
        yield Request(
            url="https://authorisation.api.bunnings.com.au/External/Callback",
            meta={
                "dont_redirect": True,
                "handle_httpstatus_list": [302],
                "apigee_client_id": apigee_client_id,
                "nonce": nonce,
            },
            callback=self.parse_idsrv_cookie_2,
        )

    def parse_idsrv_cookie_2(self, response: Response) -> Iterable[Request]:
        apigee_client_id = response.meta["apigee_client_id"]
        nonce = response.meta["nonce"]
        yield Request(
            url=f"https://authorisation.api.bunnings.com.au/connect/authorize/callback?response_type=token&scope=chk%3Aexec%20cm%3Aaccess%20ecom%3Aaccess%20chk%3Apub%20vch%3Apublic%20&client_id=budp_guest_user_au&redirect_uri=https%3A%2F%2Fwww.bunnings.com.au%2Fstatic%2Fguest.html&nonce={nonce}&acr_values=",
            meta={"dont_redirect": True, "handle_httpstatus_list": [302], "apigee_client_id": apigee_client_id},
            callback=self.parse_jwk,
        )

    def parse_jwk(self, response: Response) -> Iterable[Request]:
        apigee_client_id = response.meta["apigee_client_id"]
        location_header_url = str(response.headers.getlist("Location")[0])
        jwk = location_header_url.split("#access_token=", 1)[1].split("&token_type=", 1)[0]
        headers = {
            "Authorization": "Bearer " + jwk,
            "clientId": apigee_client_id,
            "country": "AU",
            "locale": "en_AU",
        }
        for url in self.start_urls:
            yield Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response: Response) -> Iterable[Feature]:
        if response.json()["statusDetails"]["state"] != "SUCCESS":
            return
        for location in response.json()["data"]["stores"]:
            if not location["isActiveLocation"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["name"]
            item.pop("name", None)
            item["branch"] = location["displayName"]
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            if item["country"] == "NZ":
                item.pop("state")
                website_prefix = "https://www.bunnings.co.nz/stores/"
            else:
                item["state"] = location["address"]["region"]["isocode"]
                website_prefix = "https://www.bunnings.com.au/stores/"
            if "urlRegion" in location:
                item["website"] = (
                    website_prefix + location["urlRegion"] + "/" + location["displayName"].lower().replace(" ", "-")
                )
            item["extras"]["website:map"] = location.get("mapUrl")
            item["opening_hours"] = OpeningHours()
            for day in location["openingHours"]["weekDayOpeningList"]:
                if (
                    not day["closed"]
                    and day.get("openingTime")
                    and day["openingTime"].get("formattedHour")
                    and day.get("closingTime")
                    and day["closingTime"].get("formattedHour")
                ):
                    item["opening_hours"].add_range(
                        day=day["weekDay"],
                        open_time=day["openingTime"]["formattedHour"],
                        close_time=day["closingTime"]["formattedHour"],
                        time_format="%I:%M %p",
                    )
            apply_category(Categories.SHOP_HARDWARE, item)
            yield item
