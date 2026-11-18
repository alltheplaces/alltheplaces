import re

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class AmicisUSSpider(Spider):
    name = "amicis_us"
    item_attributes = {"brand": "Amici", "brand_wikidata": "Q66133409"}
    start_urls = ["https://www.amicis.com/locations"]

    def parse(self, response):
        # Closed locations retain their addresses but no longer have ordering links.
        for row in response.xpath(
            '//main//a[contains(@href, "order.amicis.com")]/ancestor::div'
            '[contains(concat(" ", @class, " "), " sqs-row ")][1]'
        ):
            address = row.css(".sqs-html-content")[0]
            parts = [
                text.strip()
                for text in address.xpath(".//p//text()[not(ancestor::a)]").getall()
                if text.strip() and "NEW ADDRESS" not in text
            ]
            street, city, region = ", ".join(parts).rsplit(",", 2)
            state, postcode = region.strip().split()
            website = response.urljoin(address.css("a::attr(href)").get())
            text = " ".join(row.css(".sqs-html-content").xpath(".//text()").getall())
            item = Feature(
                ref=website.rstrip("/").rsplit("/", 1)[-1],
                branch=address.css("a").xpath("normalize-space(.)").get().removeprefix("Amici\u2019s "),
                street_address=street.strip(),
                city=city.strip(),
                state=state,
                postcode=postcode,
                country="US",
                phone=re.search(r"\b\d{3}-\d{3}-\d{4}\b", text).group(),
                website=website,
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(text)
            yield item
