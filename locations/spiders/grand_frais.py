import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature

# Address block is two free-text lines: a street/landmark description of
# inconsistent shape, followed by "<postcode> <city>" with an optional
# "(<country>)" suffix used for the small number of stores outside France
# (Belgium, Luxembourg).
POSTCODE_CITY_RE = re.compile(r"^(?P<postcode>L?\d{4,5})\s+(?P<city>.+?)(?:\s*\((?P<country>[^)]+)\))?$")
COUNTRY_NAMES = {"Belgique": "BE", "Luxembourg": "LU"}


class GrandFraisSpider(SitemapSpider):
    name = "grand_frais"
    item_attributes = {"brand": "Grand Frais", "brand_wikidata": "Q3114675", "name": "Grand Frais"}
    sitemap_urls = ["https://www.grandfrais.com/sitemap-store-locator.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//ol[@id="wo-breadcrumbs"]/li[2]//span[@itemprop="name"]/text()').get("")

        if m := re.search(r"waze://\?ll=(-?[\d.]+),(-?[\d.]+)", response.text):
            item["lat"], item["lon"] = m.groups()

        addr_lines = response.xpath(
            '//div[@data-content="app-point-vente-adresse"]/p[@class="sub-title mb-3"]/text()'
        ).getall()
        addr_lines = [line.strip() for line in addr_lines if line.strip()]
        if addr_lines:
            item["street_address"] = addr_lines[0]
            if m := POSTCODE_CITY_RE.match(addr_lines[-1]):
                item["postcode"] = m.group("postcode")
                item["city"] = m.group("city")
                item["country"] = COUNTRY_NAMES.get(m.group("country"), "FR")

        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/span/text()').get()

        oh = OpeningHours()
        hours_text = " ".join(
            response.xpath('//div[@data-content="app-point-vente-horaires"]/p[not(contains(@class, "circle"))]')
            .xpath("normalize-space()")
            .getall()
        )
        oh.add_ranges_from_string(hours_text, days=DAYS_FR, delimiters=DELIMITERS_FR, closed=CLOSED_FR)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
