from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

BRAND_MAPPING = {
    "Bankomat (Euronet)": ("Euronet", "Q5412010"),
    "Bankomat (Planet Cash)": ("Planet Cash", "Q117744569"),
    "Bankomat bezprowizyjny w placówce CA BP": ("Crédit Agricole", "Q590952"),
    "Bankomat bezprowizyjny": ("Crédit Agricole", "Q590952"),
}


class CreditAgricolePLSpider(SitemapSpider, StructuredDataSpider):
    name = "credit_agricole_pl"
    item_attributes = {"brand": "Crédit Agricole", "brand_wikidata": "Q590952"}
    sitemap_urls = ["https://www.credit-agricole.pl/sitemap.xml"]
    wanted_types = ["FinancialService"]
    sitemap_rules = [(r"/oddzial/[\d]+", "parse_sd"), (r"/bankomat/[\d]+", "parse_atm")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.BANK, item)
        yield item

    def parse_atm(self, response):
        item = Feature()
        item["street_address"] = response.xpath('//*[@class="street-address"]//text()').get()
        item["ref"] = item["website"] = response.url
        item["lat"] = response.xpath('//script[contains(., "branchLat")]').re_first(r"var branchLat = '([\d.]+)';")
        item["lon"] = response.xpath('//script[contains(., "branchLng")]').re_first(r"var branchLng = '([\d.]+)';")
        self.parse_atm_hours(item, response)

        atm_type = (
            response.xpath("//h1[@class='section-title title--secondary title--contact-map']/small[1]/text()")
            .get(default="")
            .strip()
        )

        if match := BRAND_MAPPING.get(atm_type):
            item["brand"], item["brand_wikidata"] = match
        else:
            self.crawler.stats.inc_value(f"atp/credit_agricole_pl/unknown_brand/{atm_type}")

        apply_category(Categories.ATM, item)
        yield item

    def parse_atm_hours(self, item, response):
        if hours := response.xpath("//p[@datetime]/@datetime").getall():
            try:
                oh = OpeningHours()
                for hour in hours:
                    oh.add_ranges_from_string(hour.replace(".", ""))
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours {hours}: {e}")
