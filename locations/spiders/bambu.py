import json
from base64 import b64encode
from gzip import compress

from scrapy import Request, Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature, SocialMedia, set_social_media


class BambuSpider(Spider):
    name = "bambu"
    item_attributes = {"brand": "Bambu", "brand_wikidata": "Q83437245"}

    # Start by acquiring a session cookie
    start_urls = ["https://www.drinkbambu.com/_api/v1/access-tokens"]

    def parse(self, response):
        # Now that we have a session cookie, send the actual request
        # TODO: This API seems to have a pagination mechanism (the response includes a cursor) but
        # I don't know how to use it. Requesting 999 results works ok for now.
        params = {
            "urlParams": {"gridAppId": "26451472-ec1e-4598-a994-03f8b5503c63"},
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
                "routerSuffix": "/",
                "fullUrl": "https://www.drinkbambu.com/properties/",
            },
        }
        query = b64encode(compress(json.dumps(params, separators=(",", ":")).encode())).decode()
        req = Request(
            f"https://www.drinkbambu.com/_api/dynamic-pages-router/v1/pages?{query}",
            callback=self.parse_pages,
        )
        req.cookies["svSession"] = response.json()["svSession"]
        yield req

    def parse_pages(self, response):
        result = response.json()["result"]
        if response.json().get("exception", False):
            raise RuntimeError(result["name"] + result["message"])
        for location in result["data"]["items"]:
            item = Feature()
            item["city"] = location["mapLocation"]["city"]
            item["lat"] = location["mapLocation"]["location"]["latitude"]
            item["lon"] = location["mapLocation"]["location"]["longitude"]
            item["housenumber"] = location["mapLocation"]["streetAddress"]["number"]
            item["street"] = location["mapLocation"]["streetAddress"]["name"]
            item["extras"]["addr:unit"] = location["mapLocation"]["streetAddress"]["apt"]
            item["country"] = location["mapLocation"]["country"]
            item["postcode"] = location["mapLocation"].get("postalCode")
            item["state"] = location["mapLocation"].get("subdivision")
            item["email"] = location["agentEmail"]
            item["ref"] = location["_id"]
            item["phone"] = location["storePhone"]
            set_social_media(item, SocialMedia.FACEBOOK, location.get("facebook"))
            set_social_media(item, SocialMedia.YELP, location.get("yelp"))
            item["addr_full"] = location["address"]
            item["branch"] = location["title"].removeprefix("Bambu ")

            if location.get("instagram") != "https://www.instagram.com/bambudessertdrinks/":
                set_social_media(item, SocialMedia.INSTAGRAM, location.get("instagram"))

            item["website"] = response.urljoin(location["link-location-pages-title"])

            oh = OpeningHours()
            for i, day in enumerate(DAYS):
                hours = location.get("storeHours" + ("1" * i), "")
                oh.add_ranges_from_string(f"{day} {hours}")
            item["opening_hours"] = oh

            yield item
