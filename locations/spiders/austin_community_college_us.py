import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# "City, TX 78701" or "City, Texas 78701" - the site is inconsistent about
# abbreviating the state, so match both and just hardcode "TX" ourselves
# below since every campus is in Central Texas.
CITY_STATE_ZIP = re.compile(r"^(?P<city>[A-Za-z .]+),\s*(?:TX|Texas)\s+(?P<postcode>\d{5})$")


class AustinCommunityCollegeUSSpider(Spider):
    name = "austin_community_college_us"
    item_attributes = {
        "brand": "Austin Community College District",
        "brand_wikidata": "Q3629946",
        "state": "TX",
    }
    start_urls = [
        "https://www.austincc.edu/campuses/cypress-creek/",
        "https://www.austincc.edu/campuses/eastview-campus/",
        "https://www.austincc.edu/campuses/elgin-campus/",
        "https://www.austincc.edu/campuses/hays-campus/",
        "https://www.austincc.edu/campuses/highland-campus/",
        "https://www.austincc.edu/campuses/acc-lockhart/",
        "https://www.austincc.edu/campuses/northridge-campus/",
        "https://www.austincc.edu/campuses/rio-grande-campus/",
        "https://www.austincc.edu/campuses/riverside-campus/",
        "https://www.austincc.edu/campuses/round-rock-campus/",
        "https://www.austincc.edu/campuses/san-gabriel-campus/",
        "https://www.austincc.edu/campuses/south-austin-campus/",
    ]

    def parse(self, response: Response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = " ".join(response.xpath("//h1//text()").getall()).strip()

        contact_lines = [
            line.strip()
            for line in response.xpath(
                '//h3[normalize-space(text())="Contact"]/parent::div/following-sibling::p[1]//text()'
            ).getall()
            if line.strip() and line.strip() != "Map"
        ]
        if not contact_lines:
            # Page doesn't follow the usual template; skip rather than yield a broken item.
            return

        item["phone"] = contact_lines[-1]
        addr_lines = contact_lines[:-1]

        if len(addr_lines) == 2 and (city_state_zip := CITY_STATE_ZIP.match(addr_lines[1])):
            item["street_address"] = addr_lines[0]
            item["city"] = city_state_zip.group("city")
            item["postcode"] = city_state_zip.group("postcode")
        else:
            # e.g. the Lockhart Center's address doesn't split cleanly into a
            # single street line and a "City, TX ZIP" line, so fall back to
            # an unsplit address rather than forcing an incorrect split.
            item["addr_full"] = ", ".join(addr_lines)
            if postcode := re.search(r"(\d{5})$", addr_lines[-1]):
                item["postcode"] = postcode.group(1)

        hours_lines = response.xpath(
            '//h3[normalize-space(text())="Hours"]/parent::div/following-sibling::p[1]//text()'
        ).getall()
        hours_text = re.sub(r"\s+", " ", " ".join(line.strip() for line in hours_lines)).strip()
        if hours_text and "class" not in hours_text.lower():
            # "Noon" isn't recognised by OpeningHours' named times, but "Midday" is.
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_text.replace("Noon", "Midday"))
            item["opening_hours"] = oh

        apply_category(Categories.COLLEGE, item)

        yield item
