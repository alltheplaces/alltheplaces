import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TaqueriaTsunamiUSSpider(Spider):
    name = "taqueria_tsunami_us"
    item_attributes = {"brand": "Taqueria Tsunami"}
    start_urls = ["https://taqueriatsunami.com/locations"]

    def parse(self, response):
        for paragraph in response.css(".sqs-html-content > p"):
            lines = [text.strip() for text in paragraph.xpath("./text()").getall() if text.strip()]
            if len(lines) != 3 or not re.fullmatch(r"\(\d{3}\)\s*\d{3}\s*-\s*\d{4}", lines[2]):
                continue
            city, region = lines[1].rsplit(",", 1)
            state, postcode = region.split()
            headings = []
            for sibling in reversed(paragraph.xpath("preceding-sibling::*")):
                if sibling.root.tag != "h3":
                    break
                headings.insert(0, sibling.xpath("normalize-space(.)").get().title())
            hours = OpeningHours()
            website = None
            for sibling in paragraph.xpath("following-sibling::*"):
                if sibling.root.tag == "h3":
                    break
                if link := sibling.xpath('.//a[normalize-space(.)="ORDER ONLINE"]/@href').get():
                    website = link
                text = " ".join(sibling.xpath(".//text()").getall())
                # Atlanta publishes implausible 11 PM openings with 9/10 PM closings.
                if city.strip() != "Atlanta":
                    hours.add_ranges_from_string(text)
            item = Feature(
                ref=website,
                branch=" - ".join(headings),
                street_address=lines[0],
                city=city.strip(),
                state=state,
                postcode=postcode,
                country="US",
                phone=lines[2],
                website=response.url,
                opening_hours=hours,
            )
            apply_category(Categories.RESTAURANT, item)
            yield item
