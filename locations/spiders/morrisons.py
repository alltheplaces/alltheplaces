import scrapy
import re
from locations.items import GeojsonPointItem

DAYS = {
    "mon": "Mo",
    "tue": "Tu",
    "wed": "We",
    "fri": "Fr",
    "thu": "Th",
    "sat": "Sa",
    "sun": "Su",
}


class MorrisonsSpider(scrapy.Spider):
    name = "morrisons"
    item_attributes = {"brand": "Morrisons", "brand_wikidata": "Q922344"}
    allowed_domains = ["api.morrisons.com"]
    start_urls = [
        "https://api.morrisons.com/location/v2//stores?apikey=kxBdM2chFwZjNvG2PwnSn3sj6C53dLEY&limit=20000"
    ]

    def store_hours(self, store_hours):
        clean_time = ""
        for key, value in store_hours.items():
            if "open" in value and "close" in value:
                if re.search("[0-9]{2}:[0-9]{2}:[0-9]{2}", value["open"]) and re.search(
                    "[0-9]{2}:[0-9]{2}:[0-9]{2}", value["close"]
                ):
                    clean_time = (
                        clean_time
                        + DAYS[key]
                        + " "
                        + value["open"][0:5]
                        + "-"
                        + value["close"][0:5]
                        + ";"
                    )
                else:
                    clean_time = clean_time + DAYS[key] + " " + "Closed" + ";"

        return clean_time

    def parse_store(self, data):
        address = ", ".join(
            filter(
                None,
                (
                    data["address"]["addressLine1"].strip(),
                    data["address"]["addressLine2"].replace("None", "").strip(),
                ),
            )
        )
        properties = {
            "street_address": address,
            "phone": data["telephone"],
            "city": data["address"]["city"].replace("None", "").strip(),
            "postcode": data["address"]["postcode"],
            "ref": data["name"],
            "name": data["storeName"],
            "country": data["address"]["country"],
            "website": "https://my.morrisons.com/storefinder/" + str(data["name"]),
            "lat": data["location"]["latitude"],
            "lon": data["location"]["longitude"],
        }

        hours = self.store_hours(data["openingTimes"])
        if hours:
            properties["opening_hours"] = hours

        return GeojsonPointItem(**properties)

    def parse(self, response):
        # may need to do pagination at some point, but right now the API accepts any limit
        for store in response.json()["stores"]:
            yield self.parse_store(store)
