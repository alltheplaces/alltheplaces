import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.spiders.auchan_fr import AuchanFRSpider
from locations.spiders.carrefour_fr import CARREFOUR_MARKET, CARREFOUR_SUPERMARKET
from locations.spiders.e_leclerc import ELeclercSpider
from locations.spiders.intermarche import IntermarcheSpider
from locations.spiders.systeme_u import SystemeUSpider


class CashServicesFRSpider(CrawlSpider):
    name = "cash_services_fr"
    item_attributes = {"brand": "Cash Services"}
    allowed_domains = ["www.cash-services.fr"]
    start_urls = ["https://www.cash-services.fr/fr/Regions.aspx"]

    LOCATED_IN_MAPPINGS = [
        (["HYPER U"], SystemeUSpider.brands["hyperu"]),
        (["SUPER U"], SystemeUSpider.brands["superu"]),
        (["U EXPRESS"], SystemeUSpider.brands["uexpress"]),
        (["INTERMARCHE"], IntermarcheSpider.INTERMARCHE),
        (["E.LECLERC"], ELeclercSpider.item_attributes),
        (["CARREFOUR MARKET"], CARREFOUR_MARKET),
        (["CARREFOUR"], CARREFOUR_SUPERMARKET),
        # Cora in France has been rebranded to Carrefour
        (["CORA"], CARREFOUR_SUPERMARKET),
        (["AUCHAN"], AuchanFRSpider.item_attributes),
    ]

    rules = [
        Rule(LinkExtractor(allow=r"/fr/Departements\.aspx")),
        Rule(LinkExtractor(allow=r"/fr/Localites\.aspx")),
        Rule(LinkExtractor(allow=r"/fr/ResultatsRechercheGeographique\.aspx")),
        Rule(LinkExtractor(allow=r"/fr/automate/"), callback="parse_atm"),
    ]

    def parse_atm(self, response):
        item = Feature()
        item["ref"] = response.url

        # Extract name from breadcrumb
        item["name"] = response.xpath('//li[@aria-current="page"]//span[@itemprop="name"]/text()').get()

        # Extract coordinates from JavaScript (_Data$Value2 = lat, _Data$Value3 = lon)
        for script in response.xpath("//script/text()").getall():
            if lat_match := re.search(r'_Data\$Value2:"([\d.]+)"', script):
                item["lat"] = lat_match.group(1)
            if lon_match := re.search(r'_Data\$Value3:"([\d.]+)"', script):
                item["lon"] = lon_match.group(1)

        # Extract address from the main address block (near the location icon, not nearby ATM cards)
        address_paragraphs = response.xpath(
            '//span[contains(@class, "ei_icon_location")]/ancestor::div[contains(@class, "fg")]/following-sibling::div/p/text()'
        ).getall()
        for i, text in enumerate(address_paragraphs):
            text = text.strip()
            if match := re.match(r"^(\d{5})\s+(.+)$", text):
                item["postcode"] = match.group(1)
                item["city"] = match.group(2)
                if i > 0:
                    item["street_address"] = address_paragraphs[i - 1].strip()
                break

        item["country"] = "FR"
        item["website"] = response.url

        services = response.xpath('//@class[contains(., "ei_rogi_picto_")]').getall()
        apply_yes_no(Extras.CASH_IN, item, any("deposit" in s for s in services))

        apply_category(Categories.ATM, item)

        item["opening_hours"] = self.parse_opening_hours(response)

        if item["name"]:
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item["name"], self.LOCATED_IN_MAPPINGS, self
            )

        yield item

    def parse_opening_hours(self, response) -> OpeningHours | None:
        oh = OpeningHours()
        hours_table = response.xpath('//table[.//th[contains(text(), "Jours")]]//tbody/tr')
        if not hours_table:
            return None
        for row in hours_table:
            day = row.xpath(".//em/text()").get()
            if not day:
                continue
            cells = row.xpath("./td[position() > 1]")
            if len(cells) == 1:
                time_range = cells[0].xpath("normalize-space(.)").get()
                if match := re.match(r"(\d{2})h(\d{2})\s*-\s*(\d{2})h(\d{2})", time_range):
                    oh.add_range(
                        DAYS_FR[day], f"{match.group(1)}:{match.group(2)}", f"{match.group(3)}:{match.group(4)}"
                    )
            elif len(cells) == 2:
                morning = cells[0].xpath("normalize-space(.)").get()
                afternoon = cells[1].xpath("normalize-space(.)").get()
                morning_closed = "fermé" in morning.lower() if morning else True
                afternoon_closed = "fermé" in afternoon.lower() if afternoon else True
                if morning_closed and afternoon_closed:
                    oh.set_closed(DAYS_FR[day])
                    continue
                if morning_match := re.match(r"(\d{2})h(\d{2})\s*-\s*(\d{2})h(\d{2})", morning):
                    oh.add_range(
                        DAYS_FR[day],
                        f"{morning_match.group(1)}:{morning_match.group(2)}",
                        f"{morning_match.group(3)}:{morning_match.group(4)}",
                    )
                if afternoon_match := re.match(r"(\d{2})h(\d{2})\s*-\s*(\d{2})h(\d{2})", afternoon):
                    oh.add_range(
                        DAYS_FR[day],
                        f"{afternoon_match.group(1)}:{afternoon_match.group(2)}",
                        f"{afternoon_match.group(3)}:{afternoon_match.group(4)}",
                    )
        return oh
