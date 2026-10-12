import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Location pages come from the site's sitemap, which also lists a private
# dining page per restaurant, the city index pages and a development page.
#
# The schema.org Restaurant record's openingHoursSpecification is malformed
# ("T12:0"), so hours are not read, and no coordinates are published.
#
# Three restaurants carry no structured data, so their address block is read
# instead. Its lines are unpunctuated, e.g. "ATLANTA GA 30361", and two of them
# publish only a street.
#
# No brand:wikidata is set because the chain has no Wikidata item.

# The two street only pages, by their path.
CITIES = {"bos-seaport": ("Boston", "MA"), "weha-blue-back-square": ("West Hartford", "CT")}


class BoqueriaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "boqueria_us"
    item_attributes = {"brand": "Boqueria"}
    allowed_domains = ["boqueriarestaurant.com"]
    sitemap_urls = ["https://boqueriarestaurant.com/sitemap.xml"]
    sitemap_rules = [(r"/location/(?!.*(?:events|catering|dev)).*/$", "parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse_sd(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        yield from super().parse_sd(response, **kwargs) or []

        if response.xpath('//script[@type="application/ld+json"][contains(text(), \'"Restaurant"\')]'):
            return

        # "1221 PEACHTREE ST NE" / "ATLANTA GA 30361", though two restaurants
        # publish only their street.
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in response.xpath('//div[@class="address-phone"]//text()').getall()
            if line.strip()
        ]
        if not lines:
            return

        item = Feature()
        item["ref"] = response.url.replace("https://boqueriarestaurant.com/location/", "").strip("/")
        item["branch"] = (response.xpath('//h1[@class="loc-name"]/text()').get("") or "").title().strip()
        item["website"] = response.url
        item["phone"] = response.xpath('//div[@class="address-phone"]//a[starts-with(@href, "tel:")]/text()').get()

        if locality := next(
            (match for line in lines if (match := re.fullmatch(r"(.+?),?\s+([A-Z]{2})\s+(\d{5})", line))), None
        ):
            item["city"], item["state"], item["postcode"] = locality.groups()
            item["street_address"] = ", ".join(lines[: lines.index(locality.group(0))])
        else:
            # Boston and West Hartford publish only their street.
            item["street_address"] = lines[0]
            item["city"], item["state"] = CITIES.get(item["ref"], (None, None))

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "spanish;tapas"

        yield item

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # The records give "WASHINGTON, DC" as the city with no region, and
        # "NYC" with the state spelled out or missing.
        if city := item.get("city"):
            if locality := re.fullmatch(r"(.+?),\s*([A-Z]{2})", city):
                item["city"], item["state"] = locality.groups()
            elif city.upper() == "NYC":
                item["city"], item["state"] = "New York", "NY"

        item["ref"] = response.url.replace("https://boqueriarestaurant.com/location/", "").strip("/")
        # "BOQUERIA SOHO"
        item["branch"] = (item.pop("name", None) or "").title().removeprefix("Boqueria").strip()
        item["website"] = response.url
        # The record's hours are malformed and its cuisine is a description.
        item["opening_hours"] = None
        item["extras"].pop("cuisine", None)
        item["image"] = None

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "spanish;tapas"

        yield item
