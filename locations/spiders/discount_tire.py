import json
import re

from scrapy import Request

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class DiscountTireSpider(StructuredDataSpider):
    name = "discount_tire"
    item_attributes = {"brand": "Discount Tire", "brand_wikidata": "Q5281735"}
    allowed_domains = ["discounttire.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        headers = {"Referer": "https://www.discounttire.com/", "Operation": "CmsPage"}

        yield Request(
            url="https://data.discounttire.com/webapi/discounttire.graph",
            method="POST",
            headers=headers,
            body=json.dumps(
                {
                    "operationName": "CmsPage",
                    "variables": {"id": "/store"},
                    "query": "query CmsPage($id: String!) {\n  cms {\n    page(id: $id) {\n      documentTitle\n      metaTags {\n        name\n        content\n        __typename\n      }\n      breadcrumbs {\n        name\n        url\n        __typename\n      }\n      htmlContent\n      source\n      __typename\n    }\n    __typename\n  }\n}\n",
                }
            ),
            callback=self.parse_sitemap,
        )

    def parse_sitemap(self, response):
        data = json.loads(response.text)
        html_content = data["data"]["cms"]["page"]["htmlContent"]
        urls = re.findall(r"href=\"(\/store\/[a-z]{2}\/[\w-]+\/s\/\d+)\"", html_content)
        for url in urls:
            new_url = "https://www.discounttire.com" + url[6:]
            headers = {"Referer": "https://www.discounttire.com/", "Operation": "CmsPage"}
            yield Request(
                url="https://data.discounttire.com/webapi/discounttire.graph",
                method="POST",
                headers=headers,
                body=json.dumps(
                    {
                        "operationName": "StoreByCode",
                        "variables": {"storeCode": url.split("/")[-1]},
                        "query": "query StoreByCode($storeCode: String!) {  store {    byCode(storeCode: $storeCode) { ...myStoreFields __typename } __typename } } fragment myStoreFields on StoreData { code address { country { isocode name __typename } email line1 line2 phone postalCode region { isocodeShort name __typename } town __typename } baseStore displayName legacyStoreCode geoPoint { latitude longitude __typename } weekDays { closed dayOfWeek __typename closingTime {        formattedHour        hour        minute        __typename    }    openingTime {        formattedHour        hour        minute        __typename    } } __typename } ",
                    }
                ),
                callback=self.parse_store,
                cb_kwargs={"url": new_url},
            )

    def parse_store(self, response, url):
        poi = response.json().get("data", {}).get("store", {}).get("byCode", {})
        item = DictParser.parse(poi)
        item["website"] = url
        item["ref"] = poi.get("code")
        if line2 := poi.get("address", {}).get("line2"):
            item["street_address"] = item["street_address"] + " " + line2
        item["phone"] = poi.get("address", {}).get("phone")
        item["email"] = poi.get("address", {}).get("email")
        item["state"] = poi.get("address", {}).get("region", {}).get("name")
        self.parse_hours(item, poi.get("weekDays", []))

        yield item

    def parse_hours(self, item, week_days):
        try:
            oh = OpeningHours()
            for day in week_days:
                if day.get("closed"):
                    continue
                opening_time = day.get("openingTime", {})
                closing_time = day.get("closingTime", {})
                oh.add_range(
                    DAYS_EN[day.get("dayOfWeek").capitalize()],
                    opening_time.get("formattedHour"),
                    closing_time.get("formattedHour"),
                    "%H:%M %p",
                )
            item["opening_hours"] = oh.as_opening_hours()
        except Exception:
            pass
