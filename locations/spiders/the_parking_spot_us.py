import re

from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class TheParkingSpotUSSpider(Spider):
    name = "the_parking_spot_us"
    item_attributes = {"brand": "The Parking Spot", "country": "US"}
    allowed_domains = ["support.theparkingspot.com"]
    start_urls = ["https://support.theparkingspot.com/api/v2/help_center/en-us/articles/34874163428759.json"]

    def parse(self, response):
        article = response.json()["article"]
        for row in Selector(text=article["body"]).xpath("//tr[td]"):
            columns = row.xpath("./td")
            if len(columns) != 3:
                continue
            facility = " ".join(columns[0].xpath(".//text()").getall()).split()
            facility = " ".join(facility)
            airport, _, location = facility.partition(" - ")
            _, _, name = location.partition(" - ")
            if not name.startswith("The Parking Spot"):
                continue

            address_lines = [" ".join(p.xpath(".//text()").getall()).strip() for p in columns[1].xpath("./p")]
            if len(address_lines) != 2 or not (
                match := re.fullmatch(r"(.+), ([A-Z]{2}) (\d{5}(?:-\d{4})?)", address_lines[1])
            ):
                self.logger.warning("Unrecognized facility address: %s", facility)
                continue

            city, state, postcode = match.groups()
            item = Feature(
                ref=f"{airport}-{name}",
                name=name,
                street_address=address_lines[0],
                city=city,
                state=state,
                postcode=postcode,
                phone=columns[2].xpath("normalize-space(.)").get(),
                website=article["html_url"],
            )
            apply_category(Categories.PARKING, item)
            yield item
