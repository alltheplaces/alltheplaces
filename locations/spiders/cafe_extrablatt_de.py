from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, DELIMITERS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CafeExtrablattDESpider(SitemapSpider, StructuredDataSpider):
    name = "cafe_extrablatt_de"
    item_attributes = {"brand": "Cafe Extrablatt", "brand_wikidata": "Q1025505"}
    sitemap_urls = ["https://cafe-extrablatt.de/sitemap.xml"]
    sitemap_rules = [(r"/standorte/details/cafe-extrablatt-.*", "parse_sd")]
    wanted_types = ["Restaurant"]
    days = DAYS_DE

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["name"] + item["phone"]
        if ld_data["openingHoursSpecification"]:
            item["opening_hours"] = OpeningHours()

            for rule in ld_data["openingHoursSpecification"]:
                range_str = (
                    rule["dayOfWeek"]
                    + " "
                    + rule["opens"].replace(" Uhr", "")
                    + "-"
                    + rule["closes"].replace(" Uhr", "")
                )
                item["opening_hours"].add_ranges_from_string(
                    ranges_string=range_str, days=DAYS_DE, delimiters=DELIMITERS_DE
                )
        yield item
