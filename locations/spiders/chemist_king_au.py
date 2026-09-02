import re
from html import unescape
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

AU_STATES = "SA|NSW|VIC|QLD|WA|TAS|NT|ACT"


class ChemistKingAUSpider(Spider):
    name = "chemist_king_au"
    item_attributes = {"brand": "Chemist King Discount Pharmacy", "brand_wikidata": "Q63367667"}
    allowed_domains = ["www.chemistking.com.au"]
    start_urls = ["https://www.chemistking.com.au/stores"]

    def parse(self, response: Response) -> Iterable[Response]:
        # The sitemap doesn't separate out store pages, so store links are found in a
        # "Stores" dropdown menu in the site nav instead. HTML classes/ids on this Wix
        # site are randomly generated per page build, so rely on link text always ending
        # with a state abbreviation in parentheses (e.g. "Frewville (SA)") rather than
        # any class name.
        for link in response.css('a[data-testid="linkElement"]'):
            text = " ".join(link.css("*::text").getall()).strip()
            if re.match(rf"^.+\(({AU_STATES})\)$", text):
                yield response.follow(link.attrib["href"], callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        # Same reasoning as above: this site's element classes/ids are randomly
        # generated, so pull data out of the visible text content instead.
        body_text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", response.text)
        text = unescape(re.sub(r"<[^>]+>", " ", body_text))
        text = text.replace("​", "").replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url

        if title := response.css("title::text").get():
            item["branch"] = re.sub(rf"\s*\(({AU_STATES})\)\s*\|.*$", "", title).strip()

        if m := re.search(rf"([0-9].{{5,100}}?),\s*({AU_STATES})\s+(\d{{4}})", text):
            prefix, state, postcode = m.groups()
            street, _, city = prefix.rpartition(",")
            item["street_address"] = street.strip() or prefix.strip()
            item["city"] = city.strip()
            item["state"] = state
            item["postcode"] = postcode

        if phone := response.css('a[href^="tel:"]::attr(href)').get():
            item["phone"] = phone.replace("tel:", "").strip()

        if m := re.search(r"Opening Hours:\s*(.*?)\s*P\s*ublic\s*Holidays:", text):
            oh = OpeningHours()
            oh.add_ranges_from_string(m.group(1))
            item["opening_hours"] = oh

        apply_category(Categories.PHARMACY, item)

        yield item
