import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The brand has no locations page; the navigation links to a page per pub,
# where the address is the text of a Google Maps link, followed by the phone
# and an email.
#
# Four pubs wrap that address in the link and three give it as plain text, and
# one splits the street from the city onto separate lines. The site header
# repeats one pub's address and phone on every page, so both are read from the
# pub's own paragraphs first.
#
# No coordinates or hours are published: the map links are Google short links.
#
# No brand:wikidata is set because the chain has no Wikidata item.

ADDRESS = re.compile(r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})")
CITY = re.compile(r"([^,]+),\s*([A-Z]{2})\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class LittlePubUSSpider(Spider):
    name = "little_pub_us"
    item_attributes = {"brand": "Little Pub"}
    allowed_domains = ["littlepub.com"]
    start_urls = ["https://littlepub.com/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in sorted(set(response.xpath("//a/@href").re(r"^/[a-z-]+$"))):
            if path.strip("/") in {"about", "catering", "contact", "events", "gallery", "menu", "menus"}:
                continue
            yield response.follow(path, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        lines = [
            re.sub(r"\s+", " ", " ".join(line.xpath(".//text()").getall())).strip() for line in response.xpath("//p")
        ]
        lines = [line for line in lines if line]

        # Most pubs give "street, city, ST postcode" on one line; one splits
        # the street onto the line above.
        locality = next((index for index, line in enumerate(lines) if ADDRESS.fullmatch(line)), None)
        if locality is not None:
            street, city, state, postcode = ADDRESS.fullmatch(lines[locality]).groups()
        else:
            locality = next((index for index, line in enumerate(lines) if CITY.fullmatch(line)), None)
            if locality is None or locality == 0:
                return
            city, state, postcode = CITY.fullmatch(lines[locality]).groups()
            street = lines[locality - 1]

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["street_address"], item["city"], item["state"], item["postcode"] = street, city, state, postcode
        item["website"] = response.url
        # "Little Pub Wilton"
        heading = re.sub(r"\s+", " ", response.xpath("//h3/text()").get("") or "").strip()
        item["branch"] = re.sub(r"(?i)^little pub\s*", "", heading).strip() or item["ref"].replace("-", " ").title()
        # The site header carries one pub's phone as a tel: link on every page,
        # so the pub's own number is read from its paragraphs first.
        item["phone"] = next((line for line in lines if PHONE.fullmatch(line)), None) or response.xpath(
            '//a[starts-with(@href, "tel:")]/@href'
        ).re_first(r"tel:(.+)")
        # The email is unreliable: most pages show "info@littlepub.com" while
        # their mailto link carries another pub's address, so it is not used.

        apply_category(Categories.PUB, item)
        item["extras"]["cuisine"] = "american"

        yield item
