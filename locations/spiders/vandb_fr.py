from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Source JSON-LD hardcodes addressCountry to "FR" for every branch, but a handful are
# actually elsewhere: 2 in Réunion (ISO country RE, not FR) and 1 in Northampton, UK -
# whose page also carries a bogus postcode copy-pasted from the FR head office's.
COUNTRY_OVERRIDES = {
    "v-and-b-st-denis": "RE",
    "v-and-b-st-pierre": "RE",
    "v-and-b-northampton": "GB",
}


class VandbFRSpider(SitemapSpider, StructuredDataSpider):
    name = "vandb_fr"
    item_attributes = {"brand": "V and B", "brand_wikidata": "Q100706329"}
    sitemap_urls = ["https://www.vandb.fr/sitemap.xml"]
    # "centrale" (head office) has no "v-and-b-" slug, so it's excluded here already.
    sitemap_rules = [(r"/nos-magasins/(v-and-b-[a-z0-9-]+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").removeprefix("V and B ")
        apply_category(Categories.SHOP_ALCOHOL, item)

        if country := COUNTRY_OVERRIDES.get(item["ref"]):
            item["country"] = country
            if item["ref"] == "v-and-b-northampton":
                item["postcode"] = None

        # Opening hours aren't in the JSON-LD; scrape the HTML hours grid instead.
        # A handful of listed stores show "Fermé" on all 7 days with no exceptional-closure
        # note - that's an unfilled-in listing, not a real weekly closure, so leave hours unset.
        hour_rows = []
        for row in response.xpath('//h2[contains(text(), "Horaires")]/following-sibling::div[1]/div'):
            day = row.xpath("./span[1]/text()").get("").strip()
            hours = row.xpath("./span[2]/text()").get("").strip()
            if day in DAYS_FR:
                hour_rows.append((DAYS_FR[day], hours))

        if hour_rows and not all("ferm" in hours.lower() for _, hours in hour_rows):
            item["opening_hours"] = OpeningHours()
            for day, hours in hour_rows:
                if "ferm" in hours.lower():
                    item["opening_hours"].set_closed(day)
                    continue
                times = [t.strip().replace("h", ":") for t in hours.split(" - ")]
                for open_time, close_time in zip(times[0::2], times[1::2]):
                    item["opening_hours"].add_range(day, open_time, close_time)

        yield item
