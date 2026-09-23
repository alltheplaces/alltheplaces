import base64
import json
import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AnthonyVinceNailSpaUSSpider(Spider):
    name = "anthony_vince_nail_spa_us"
    item_attributes = {"brand": "Anthony Vince' Nail Spa", "name": "Anthony Vince' Nail Spa"}
    start_urls = ["https://www.anthonyvincenailspa.com/_api/v1/access-tokens"]

    def parse(self, response):
        access_tokens = response.json()
        app_id, authorization = next(
            (app_id, app["instance"])
            for app_id, app in access_tokens["apps"].items()
            if app["instance"].startswith("wixcode-pub.")
        )
        query = {
            "dataCollectionId": "Location",
            "query": {"paging": {"limit": 1000}},
            "environment": "LIVE",
            "appId": app_id,
        }
        encoded_query = base64.b64encode(json.dumps(query).encode()).decode()
        yield Request(
            f"https://www.anthonyvincenailspa.com/_api/cloud-data/v2/items/query?.r={encoded_query}",
            headers={
                "Cookie": f"svSession={access_tokens['svSession']}; hs={access_tokens['hs']}",
                "authorization": authorization,
            },
            callback=self.parse_locations,
        )

    def parse_locations(self, response):
        for data_item in response.json()["dataItems"]:
            location = data_item["data"]
            if self.is_sister_brand(location) or location["operatingHours"].strip().upper() == "CLOSED":
                continue

            address = location["address"]
            coordinates = address.get("location", {})
            street_address = address.get("streetAddress", {})
            item = Feature(
                ref=location["_id"],
                branch=location["f"],
                lat=coordinates.get("latitude"),
                lon=coordinates.get("longitude"),
                housenumber=street_address.get("number"),
                street=street_address.get("name"),
                unit=street_address.get("apt"),
                city=address.get("city") or location.get("city"),
                state=address.get("subdivision") or location.get("state", "").strip(),
                postcode=address.get("postalCode") or location.get("zipcode"),
                country=address.get("country", "US"),
                addr_full=address.get("formatted"),
                phone=location.get("phoneNumber"),
                website=response.urljoin(location.get("link-location-title") or "/locations"),
            )

            item["opening_hours"] = self.parse_hours(location["operatingHours"])
            apply_category(Categories.SHOP_BEAUTY, item)
            yield item

    @staticmethod
    def is_sister_brand(location):
        company = location.get("title", "")
        branch = location.get("f", "")
        return re.match(r"^(MV |M\.V|Prive|Venetian)", company, re.I) or re.search(r"M\.?\s*Vinc", branch, re.I)

    @staticmethod
    def parse_hours(hours_string):
        hours_string = hours_string.split("**", 1)[0].replace("\xa0", " ")
        hours_string = re.sub(r"\b(\d{1,2})(\d{2})\s*([AP])\.?M\.?", r"\1:\2 \3M", hours_string, flags=re.I)
        hours_string = re.sub(r"\b(\d{1,2})\s*([AP])\.?M\.?", r"\1 \2M", hours_string, flags=re.I)
        # A few Sunday entries have midnight or late-night typos for otherwise daytime hours.
        hours_string = re.sub(r"SUN(DAY)? 12 AM", "SUN 12 PM", hours_string, flags=re.I)
        hours_string = re.sub(r"SUN(DAY)? 11 PM", "SUN 11 AM", hours_string, flags=re.I)

        hours = OpeningHours()
        hours.add_ranges_from_string(hours_string)
        return hours
