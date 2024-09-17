from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BackhausNahrstedtDESpider(CrawlSpider, StructuredDataSpider):
    name = "backhaus_nahrstedt_de"
    item_attributes = {"brand": "Backhaus Nahrstedt", "brand_wikidata": "Q798438"}
    allowed_domains = ["nahrstedt.de"]
    start_urls = ["https://nahrstedt.de/standorte"]
    rules = [Rule(LinkExtractor(allow=r"/standorte/([\w-]+)$"), callback="parse_sd")]
    wanted_types = ["Bakery"]
    search_for_facebook = False
    search_for_email = False

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["@id"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        if len(ld_data.keys()) == 3:
            return None  # 2 Microdata blobs on the page, the first is unwanted

        item["street_address"], item["city"] = item["city"], item["street_address"]
        item["email"] = None

        if "openingHoursSpecification" in ld_data:
            item["opening_hours"] = OpeningHours()
            for rule in ld_data["openingHoursSpecification"]:
                if "Feiertag" in rule["dayOfWeek"]:
                    pass
                else:
                    item["opening_hours"].add_range(DAYS_DE[rule["dayOfWeek"]], rule["opens"], rule["closes"])

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
