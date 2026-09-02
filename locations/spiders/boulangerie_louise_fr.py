import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature

# The single-location map widget embeds a small JS object per page with the
# post's numeric ID and its lat/lng, e.g.:
#   "locations":[{"ID":"3190",...,"lat":"49.011482","lng":"1.169983",...}]
LOCATION_JS_RE = re.compile(r'"locations":\[\{"ID":"(\d+)".*?"lat":"([\-\d.]+)","lng":"([\-\d.]+)"')


class BoulangerieLouiseFRSpider(SitemapSpider):
    name = "boulangerie_louise_fr"
    item_attributes = {"brand": "Boulangerie Louise", "brand_wikidata": "Q127591514"}
    sitemap_urls = ["https://www.boulangerielouise.com/boulangerie-sitemap.xml"]
    sitemap_rules = [(r"/boulangerie/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url

        if m := LOCATION_JS_RE.search(response.xpath('//script[contains(text(), "gmwMapObjects")]/text()').get("")):
            item["ref"], item["lat"], item["lon"] = m.groups()

        item["branch"] = (
            response.xpath('//div[@class="section-title"]/div[@class="h3"]/text()')
            .get("")
            .strip()
            .removeprefix("Boulangerie Louise")
            .strip()
        )

        # Free text with an inconsistent format across branches (comma-separated or not,
        # postcode/country present or not) - not safe to split into street/city/postcode.
        # See SPECS.md for the range of formats seen.
        if addr_full := response.xpath(
            '//div[@class="section-title"]/i[contains(@class, "fa-map-marker")]/following-sibling::text()[1]'
        ).get():
            item["addr_full"] = addr_full.strip()

        item["phone"] = response.xpath(
            '//div[@class="section-title"]/i[contains(@class, "fa-phone")]/following-sibling::text()[1]'
        ).get()
        item["email"] = response.xpath(
            '//div[@class="section-title"]/i[contains(@class, "fa-envelope")]/following-sibling::text()[1]'
        ).get()

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//table[contains(@class, "table-striped")]//tr'):
            cells = row.xpath("./td")
            if len(cells) < 2:
                continue
            day = " ".join(cells[0].xpath(".//text()").getall())
            hours = " ".join(cells[1].xpath(".//text()").getall())
            if not (day := sanitise_day(day.strip(), DAYS_FR)):
                continue
            hours = hours.strip()
            if hours.lower() in CLOSED_FR:
                item["opening_hours"].add_range(day, hours, hours, closed=CLOSED_FR)
                continue
            if "-" not in hours:
                continue
            # Round hours are sometimes written without minutes, e.g. "8h - 20h".
            open_time, close_time = (re.sub(r"(?<=h)$", "00", t.strip()) for t in hours.split("-", 1))
            try:
                item["opening_hours"].add_range(day, open_time, close_time, time_format="%Hh%M")
            except ValueError:
                continue

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
