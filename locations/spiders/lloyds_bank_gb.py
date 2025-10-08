from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LloydsBankGBSpider(SitemapSpider, StructuredDataSpider):
    name = "lloyds_bank_gb"
    item_attributes = {
        "brand": "Lloyds Bank",
        "brand_wikidata": "Q1152847",
    }
    sitemap_urls = ["https://branches.lloydsbank.com/sitemap.xml"]
    sitemap_rules = [(r"https://branches\.lloydsbank\.com/[^/]+/[^/]+", "parse_sd")]
    drop_attributes = {"image"}

    def sitemap_filter(self, entries):
        for entry in entries:
            if "event" not in entry["loc"]:
                if "phone" in entry:
                    if entry["phone"].replace(" ", "").startswith("+443"):
                        entry.pop("phone", None)
                yield entry

    def pre_process_data(self, ld_data: dict, **kwargs):
        opening_hours = []
        for rule in ld_data.get("openingHours", []):
            opening_hours.append(rule.replace(".", ":"))
        ld_data["openingHours"] = opening_hours

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        location_type = response.xpath('//*[@class="LocationName-brand"]/text()').get("").strip()
        if any(
            bank in location_type for bank in ["Halifax", "Bank of Scotland"]
        ):  # Skip locations already covered by their individual brand spiders
            return

        if location_type == "Cash In & Out Machine":
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, True)
            apply_yes_no(Extras.CASH_OUT, item, True)
        elif location_type == "Cashpoint®":
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)

        yield item
