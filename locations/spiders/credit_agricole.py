import json
from datetime import date

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CreditAgricoleSpider(SitemapSpider, StructuredDataSpider):
    name = "credit_agricole"
    item_attributes = {"brand": "Crédit Agricole", "brand_wikidata": "Q590952"}
    allowed_domains = ["credit-agricole.fr"]
    sitemap_urls = ["https://www.credit-agricole.fr/robots.txt"]
    sitemap_rules = [(r"/particulier/agence/[-\w]+/([-\w]+)\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Agence Crédit Agricole ")

        if geodata := response.xpath('//div[@class="npc-sl-strct-map Card js-CardAgencyMap"]/@data-value').get():
            coords = json.loads(geodata)
            item["lat"] = coords["latitude"]
            item["lon"] = coords["longitude"]

        if schedule := response.xpath("//script/text()").re_first(r"const horaires = (\[.*\]);"):
            item["opening_hours"] = self.parse_opening_hours(json.loads(schedule))

        services = [s.lower() for s in response.xpath('//span[@class="npc-sl-strct-srv-card--text "]/text()').getall()]
        apply_yes_no(
            Extras.ATM,
            item,
            any(("distributeur" in s and "billets" in s) or ("guichet" in s and "automatique" in s) for s in services),
        )
        apply_yes_no(Extras.WHEELCHAIR, item, any("accès handicapé" in s for s in services))
        apply_yes_no(Extras.CASH_IN, item, any("dépôt" in s and "billets" in s for s in services))
        apply_category(Categories.BANK, item)

        yield item

    @staticmethod
    def parse_opening_hours(schedule: list[dict]) -> OpeningHours:
        # The schedule lists the coming weeks day by day; the first ordinary day
        # of each weekday stands for it, a bank holiday does not.
        oh = OpeningHours()
        seen = set()
        for day in schedule:
            weekday = DAYS[date.fromisoformat(day["date"]).weekday()]
            if weekday in seen or day["type"] not in ("OUVERT", "FERME"):
                continue
            seen.add(weekday)
            for slot in (day.get("matin"), day.get("apresMidi")):
                # A slot with a typeOuverture is not open to walk-in customers:
                # by appointment only (OUV_RDV), remote advice only (CONSEIL_DIST)
                # or temporarily closed (FERM_TEMPO).
                if slot and not slot.get("typeOuverture"):
                    oh.add_range(
                        weekday,
                        "{heures:02}:{minutes:02}".format(**slot["ouverture"]),
                        "{heures:02}:{minutes:02}".format(**slot["fermeture"]),
                    )
        return oh
