import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class CanadianTireCASpider(SitemapSpider):
    name = "canadian_tire_ca"
    item_attributes = {
        "brand": "Canadian Tire",
        "brand_wikidata": "Q1032400",
        "extras": Categories.SHOP_DEPARTMENT_STORE.value,
    }
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
        location = response.json()
        if not location.get("id"):
            return  # Some locations are null responses (just some fields all set to None)
        item = DictParser.parse(location)
        item["street_address"] = clean_address(
            [location.get("address", {}).get("line1"), location.get("address", {}).get("line2")]
        )
        item["city"] = location.get("address", {}).get("town")
        item["state"] = location.get("address", {}).get("region", {}).get("name")
        item["country"] = location.get("address", {}).get("country", {}).get("isocode")
        item["phone"] = location.get("address", {}).get("phone")
        item["email"] = location.get("address", {}).get("email")
        item["website"] = "https://www.canadiantire.ca" + location.get("url")
        item["opening_hours"] = OpeningHours()
        if location.get("storeServices"):
            for day in location.get("storeServices", {})[0].get("weekDayOpeningList"):
                if day.get("closed"):
                    continue
                item["opening_hours"].add_range(
                    day=day.get("weekDay"),
                    open_time=day.get("openingTime", {}).get("formattedHour").replace(".", ""),
                    close_time=day.get("closingTime", {}).get("formattedHour").replace(".", ""),
                    time_format="%I:%M %p",
                )

        yield item
