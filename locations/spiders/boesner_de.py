import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BoesnerDESpider(CrawlSpider, StructuredDataSpider):
    name = "boesner_de"
    item_attributes = {"brand": "Boesner", "brand_wikidata": "Q890317"}
    start_urls = ["https://www.boesner.com/unsere-standorte"]
    rules = [Rule(LinkExtractor(allow=r"/unsere-standorte/[^/]+$"), callback="parse_sd")]
    wanted_types = ["HobbyShop"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if not item.get("lat") or not item.get("lon"):
            return

        # Clean up name: "Niederlassung Freiburg | boesner.com" -> branch
        name = item.pop("name", "") or ""
        name = re.sub(r"^Niederlassung\s+", "", name)
        name = re.sub(r"\s*\|\s*boesner\.com$", "", name, flags=re.IGNORECASE)
        name = name.strip()

        # Skip non-retail locations (holding/corporate offices, mail-order)
        if re.search(r"Holding|Versandservice", name, re.IGNORECASE):
            return

        item["branch"] = name

        # Parse the plain-text address string
        addr_full = item.pop("addr_full", None)
        if addr_full:
            lines = [line.strip() for line in addr_full.strip().splitlines() if line.strip()]
            # Format: company / description lines, then street, then postcode+city, then country
            if len(lines) >= 3:
                country_line = lines[-1]
                postcode_city_line = lines[-2]
                street_line = lines[-3]

                m = re.match(r"(\d{4,5})\s+(.+)", postcode_city_line)
                if m:
                    item["postcode"] = m.group(1)
                    item["city"] = m.group(2)

                item["street_address"] = street_line

                country_map = {
                    "Deutschland": "DE",
                    "Österreich": "AT",
                    "Schweiz": "CH",
                    "Frankreich": "FR",
                    "Dänemark": "DK",
                    "Schweden": "SE",
                }
                item["country"] = country_map.get(country_line, country_line)

        apply_category(Categories.SHOP_CRAFT, item)
        yield item
