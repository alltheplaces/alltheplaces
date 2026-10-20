from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FigarosPizzaUSSpider(Spider):
    name = "figaros_pizza_us"
    item_attributes = {"brand": "Figaro's Pizza", "brand_wikidata": "Q48802600"}
    start_urls = [
        "https://figaros.com/stat/api/locations/search?lng=-98.5795&lat=39.8283&kilometers=8000&limit=500&fields="
    ]

    def parse(self, response):
        for location in response.json()["locations"]:
            address = location["businessAddress"]
            if address["addressCountry"] != "US":
                continue

            item = Feature(
                ref=location["locationId"],
                branch=(
                    location["businessName"].removeprefix("Figaro's Pizza ")
                    if location["businessName"] != "Figaro's Pizza"
                    else None
                ),
                street_address=address["streetAddress"],
                city=address["addressLocality"],
                state=address["addressRegion"],
                postcode=address["postalCode"],
                country=address["addressCountry"],
                lat=location["coordinates"][1],
                lon=location["coordinates"][0],
                phone=location.get("primaryPhone"),
                website=response.urljoin(location["link"]),
            )

            hours = OpeningHours()
            for day, schedule in location["hours"].items():
                if schedule["status"] == "Open":
                    for block in schedule["blocks"]:
                        start, end = block["from"], block["to"]
                        hours.add_range(day, f"{start[:2]}:{start[2:]}", f"{end[:2]}:{end[2:]}")
            item["opening_hours"] = hours

            apply_category(Categories.FAST_FOOD, item)
            yield item
