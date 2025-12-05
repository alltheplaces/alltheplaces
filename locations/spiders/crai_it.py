from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_IT, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class CraiITSpider(SitemapSpider, StructuredDataSpider):
    name = "crai_it"
    item_attributes = {"brand": "Crai", "brand_wikidata": "Q3696429"}
    sitemap_urls = ["https://crai.it/negozi-e-volantini/sitemap.xml"]

    def pre_process_data(self, ld_data, **kwargs):
        opening_hours = ld_data.get("openingHoursSpecification")

        if opening_hours:
            if all(all(key in rule for key in ["dayOfWeek", "opens", "closes"]) for rule in opening_hours):
                for rule in opening_hours:
                    rule["dayOfWeek"] = sanitise_day(rule["dayOfWeek"], DAYS_IT)
                    if "/" in rule["closes"]:
                        rule["closes"] = rule["closes"].split("/")[1]
            else:
                ld_data["openingHoursSpecification"] = None
