import json
from base64 import b64encode
from gzip import compress

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import SocialMedia, set_social_media


class BambuSpider(Spider):
    name = "bambu"
    item_attributes = {"brand": "Bambu", "brand_wikidata": "Q83437245"}

    # Start by acquiring a session cookie
    start_urls = ["https://www.drinkbambu.com/_api/v1/access-tokens"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        # Now that we have a session cookie, send the actual request
        # TODO: This API seems to have a pagination mechanism (the response includes a cursor) but
        # I don't know how to use it. Requesting 999 results works ok for now.
        params = {
            "urlParams": {"viewMode": "site"},
            "body": {
                "routerPrefix": "/properties",
                "config": {
                    "patterns": {
                        "/": {
                            "pageRole": "2ce8cb33-8752-4449-94d9-2d91ce00e549",
                            "title": "Properties",
                            "config": {
                                "collection": "Properties",
                                "pageSize": 999,
                            },
                        }
                    }
                },
                "pageRoles": {"2ce8cb33-8752-4449-94d9-2d91ce00e549": {"id": "q4yo6", "title": "Stores (All)"}},
                "requestInfo": {"formFactor": "desktop"},
                "fullUrl": "https://www.drinkbambu.com/properties/",
            },
        }
        query = b64encode(compress(json.dumps(params, separators=(",", ":")).encode())).decode()
        access_tokens = response.json()
        authorization = [
            app["instance"] for app in access_tokens["apps"].values() if app["instance"].startswith("wixcode-pub.")
        ][0]
        req = Request(
            f"https://www.drinkbambu.com/_api/dynamic-pages-router/v1/pages?{query}",
            headers={"authorization": authorization},
            callback=self.parse_pages,
        )
        req.cookies["svSession"] = access_tokens["svSession"]
        yield req

    def parse_pages(self, response):
        result = response.json()["result"]
        if response.json().get("exception", False):
            raise RuntimeError(result["name"] + result["message"])
        for location in result["data"]["items"]:
            location.update(location.pop("mapLocation", {}))
            item = DictParser.parse(location)
            street_address = location.get("streetAddress", {})
            item["housenumber"] = street_address.get("number")
            item["street"] = street_address.get("name")
            item["street_address"] = street_address.get("formattedAddressLine")
            item["extras"]["addr:unit"] = street_address.get("apt")
            if email := location.get("agentEmail"):
                if "@" in email:
                    item["email"] = email
            item["ref"] = location["_id"]
            item["phone"] = location.get("storePhone")
            set_social_media(item, SocialMedia.FACEBOOK, location.get("facebook"))
            set_social_media(item, SocialMedia.YELP, location.get("yelp"))
            item["addr_full"] = location.get("address")
            item["branch"] = location.get("title", "").removeprefix("Bambu ")
            item.pop("name")

            if location.get("instagram") != "https://www.instagram.com/bambudessertdrinks/":
                set_social_media(item, SocialMedia.INSTAGRAM, location.get("instagram"))

            item["website"] = response.urljoin(location.get("link-location-pages-title"))

            oh = OpeningHours()
            for i, day in enumerate(DAYS):
                hours = location.get("storeHours" + ("1" * i), "")
                oh.add_ranges_from_string(f"{day} {hours}")
            item["opening_hours"] = oh
            yield item
