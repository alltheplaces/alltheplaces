import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page groups its restaurants under a heading per state, each
# card giving the branch, a one line address, a phone and the restaurant's page.
#
# The address lines are inconsistently punctuated: some separate the city with
# a comma and some do not ("3330 Cobb Parkway Northwest Acworth, GA 30101"), so
# the city is taken from the branch name and stripped off the end of the line.
#
# Restaurants that have not opened are marked in the branch name, sometimes
# with an address already listed, and are skipped on that marker.
#
# No coordinates or hours are published on this page.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class BiscuitBellyUSSpider(Spider):
    name = "biscuit_belly_us"
    item_attributes = {"brand": "Biscuit Belly"}
    allowed_domains = ["biscuitbelly.com"]
    start_urls = ["https://biscuitbelly.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for card in response.xpath('//div[@class="location__item"]'):
            address = re.sub(
                r"\s+", " ", " ".join(card.xpath('.//div[@class="location__item-head"]/p//text()').getall())
            ).strip()
            # "... AL 35244" always ends the line, however it is punctuated.
            if not (locality := re.search(r"\b([A-Z]{2}),?\s+(\d{5})$", address)):
                continue

            name = re.sub(r"\s+", " ", card.xpath(".//h3//text()").get("")).strip()
            # Some restaurants that have not opened still list their address.
            if re.search(r"(?i)coming soon|opening|opens", name):
                continue
            # "Charlotte – Elizabeth", "Wake Forest (Coming Soon)"
            city = re.split(r"\s*[\u2013-]\s*|\s*\(", name)[0].strip()

            item = Feature()
            item["branch"] = name
            item["city"] = city
            item["state"], item["postcode"] = locality.groups()
            item["website"] = card.xpath(".//h3/a/@href").get()
            item["ref"] = (item["website"] or "").rstrip("/").rsplit("/", 1)[-1]
            if phone := card.xpath('.//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)"):
                item["phone"] = phone

            # The line reads "street, city" where it is punctuated, and
            # "street city" where it is not, in which case the city is taken
            # from the branch name.
            head = address[: locality.start()].strip(" ,")
            street, _, tail = head.rpartition(",")
            if street and not re.search(r"\d", tail):
                item["street_address"] = street.strip(" ,")
                item["city"] = tail.strip()
            else:
                if head.lower().endswith(city.lower()):
                    head = head[: -len(city)]
                item["street_address"] = head.strip(" ,")

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "breakfast;american"

            yield item
