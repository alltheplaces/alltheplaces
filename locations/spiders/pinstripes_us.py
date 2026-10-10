import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class PinstripesUSSpider(Spider):
    name = "pinstripes_us"
    item_attributes = {"brand": "Pinstripes", "country": "US"}
    allowed_domains = ["www.pinstripes.com"]
    start_urls = ["https://www.pinstripes.com/"]

    def parse(self, response):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for location in data["props"]["pageProps"]["homePage"]["allLocations"]:
            slug = location["slug"]["current"]
            yield response.follow(slug, self.parse_location, cb_kwargs={"ref": slug})

    def parse_location(self, response, ref):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        location = data["props"]["pageProps"]["location"]
        if location.get("isComingSoon"):
            return

        address = location["address"]
        item = Feature(
            ref=ref,
            name=self.item_attributes["brand"],
            branch=location["name"],
            street_address=address["street1"],
            city=address["city"],
            state=address["state"],
            postcode=address["zipCode"],
            phone=location["phoneNumbers"]["primary"],
            website=response.url,
        )

        hours = OpeningHours()
        for day, times in location["businessHours"].items():
            hours.add_ranges_from_string(f"{day} {times}")
        if hours.as_opening_hours():
            item["opening_hours"] = hours

        apply_category(Categories.RESTAURANT, item)
        apply_category(Categories.BOWLING, item)
        item["extras"]["cuisine"] = "italian;american"
        yield item
