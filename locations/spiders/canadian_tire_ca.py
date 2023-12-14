import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class CanadianTireCASpider(SitemapSpider):
    name = "canadian_tire_ca"
    item_attributes = {"brand": "Canadian Tire", "brand_wikidata": "Q1032400"}
    allowed_domains = ["canadiantire.ca"]
    sitemap_urls = ["https://www.canadiantire.ca/sitemap_Store-en_CA-CAD.xml"]
    sitemap_rules = [("", "parse_store_details")]
    requires_proxy = True  # Data centre IP ranges appear to be blocked (time out)
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": BROWSER_DEFAULT,
            "baseSiteId": "CTR",
            "Ocp-Apim-Subscription-Key": "c01ef3612328420c9f5cd9277e815a0e",
        }
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            # Exclude bad pages eg https://www.canadiantire.ca/en/store-details/null/-979.html
            if ref := re.search(r"\w\-(\d+).html$", entry["loc"]):
                if ref.group(1) in ["949"]:  # Test store
                    continue
                entry["loc"] = "https://apim.canadiantire.ca/v1/store/store/{}?lang=en_CA".format(ref.group(1))
                yield entry

    def parse_store_details(self, response):
        item = DictParser.parse(response.json())
        item["street_address"] = ", ".join(
            filter(
                None, [response.json().get("address", {}).get("line1"), response.json().get("address", {}).get("line2")]
            )
        )
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

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

        yield item
