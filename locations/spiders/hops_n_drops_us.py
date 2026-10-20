from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class HopsNDropsUSSpider(Spider):
    name = "hops_n_drops_us"
    item_attributes = {"brand": "Hops n Drops"}
    start_urls = [
        "https://api.appfront.ai/BeengoWebService/rest/BusinessService/getAllBranches/"
        "businessId=67e9bdaa06966697d184aeac?imagePreview=false"
    ]

    location_slugs = {
        "Lacamas": "vancouver",
        "Spokane North": "spokane-northpointe",
        "Spokane Valley": "spokane-valley-mall",
    }

    def parse(self, response):
        for location in response.json():
            if not location["isDisplayed"]:
                continue

            address = location["deliveryAddress"]
            slug = self.location_slugs.get(location["name"], location["name"].strip().lower().replace(" ", "-"))
            item = Feature(
                ref=location["id"],
                branch=location["name"].strip(),
                street_address=location["address"].rsplit(",", 2)[0].strip(),
                city=address["city"],
                state=address["state"],
                postcode=address["zipCode"],
                country="US",
                lat=location["latitude"],
                lon=location["longitude"],
                phone=location["phoneNumber"],
                website=f"https://hopsndrops.com/find-us/{slug}/",
            )

            hours = OpeningHours()
            for rule in location["detailedOpenHours"]["openHours"]:
                hours.add_range(DAYS_FROM_SUNDAY[rule["day"]], rule["openHour"], rule["closeHour"])
            item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)
            yield item
