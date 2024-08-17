from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BackhausNahrstedtDESpider(CrawlSpider, StructuredDataSpider):
    name = "backhaus_nahrstedt_de"
    item_attributes = {"brand": "Backhaus Nahrstedt", "brand_wikidata": "Q798438", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = ["nahrstedt.de"]
    start_urls = ["https://nahrstedt.de/standorte"]
    wanted_types = ["Bakery"]
    days = DAYS_DE
    rules = [
        Rule(
            LinkExtractor(allow=r"\/standorte\/[\w-]+$"),
            callback="parse_sd",
        ),
    ]
    no_refs = True # TODO: I am very confused as to why I have to do this.

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"] is None:
            item["name"] = item["city"]
        if "openingHoursSpecification" in ld_data:
            item["opening_hours"] = OpeningHours()
            for rule in ld_data["openingHoursSpecification"]:
                if "Feiertag" in rule["dayOfWeek"]:
                    pass
                else:
                    item["opening_hours"].add_range(DAYS_DE[rule["dayOfWeek"]], rule["opens"], rule["closes"])

        yield(item)