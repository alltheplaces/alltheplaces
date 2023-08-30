import re

from scrapy.http import JsonRequest
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class CanadianTireSpiderCA(SitemapSpider):
    name = "canadian_tire_ca"
    item_attributes = {"brand": "Canadian Tire", "brand_wikidata": "Q1032400"}
    allowed_domains = ["canadiantire.ca"]
    sitemap_urls = [
        "https://www.canadiantire.ca/sitemap_Store-en_CA-CAD.xml"
    ]
    sitemap_rules = [("", "parse_store")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.canadiantire.ca",
            "User-Agent": BROWSER_DEFAULT,
        },
    }

    def parse_store(self, response):
        headers = {
            "User-Agent": BROWSER_DEFAULT,
            "Host": "apim.canadiantire.ca",
            "baseSiteId": "CTR",
            "Ocp-Apim-Subscription-Key": "c01ef3612328420c9f5cd9277e815a0e",
        }
        id_url = re.findall("[0-9]+", response.url)[0]
        template = "https://apim.canadiantire.ca/v1/store/store/{id_url}?lang=en_CA"
        yield JsonRequest(url=template.format(id_url=id_url), headers=headers, callback=self.parse_store_details)

    def parse_store_details(self, response):
        item = DictParser.parse(response.json())
        item["lat"] = response.json().get("geoPoint", {}).get("latitude")
        item["lon"] = response.json().get("geoPoint", {}).get("longitude")
        item["street_address"] = ", ".join(filter(None, [response.json().get("address", {}).get("line1"), response.json().get("address", {}).get("line2")]))
        item["city"] = response.json().get("address", {}).get("town")
        item["state"] = response.json().get("address", {}).get("region", {}).get("name")
        item["country"] = response.json().get("address", {}).get("country", {}).get("isocode")
        item["phone"] = response.json().get("address", {}).get("phone")
        item["email"] = response.json().get("address", {}).get("email")
        item["website"] = "https://www.canadiantire.ca" + response.json().get("url")
        item["opening_hours"] = OpeningHours()
        if response.json().get("storeServices"):
            for day in response.json().get("storeServices", {})[0].get("weekDayOpeningList"):
                if day.get("closed"):
                    continue
                item["opening_hours"].add_range(
                    day=day.get("weekDay"),
                    open_time=day.get("openingTime", {}).get("formattedHour").replace(".", ""),
                    close_time=day.get("closingTime", {}).get("formattedHour").replace(".", ""),
                    time_format="%I:%M %p",
                )
        yield item
