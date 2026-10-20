import re
from typing import Any
from urllib.parse import unquote

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

TIME_RANGE = re.compile(r"(\d{1,2})h(\d{2})\s*-\s*(\d{1,2})h(\d{2})")
POSTCODE = re.compile(r"^(\d{4}-\d{3})\s+(.+)$")


class MontepioPTSpider(Spider):
    name = "montepio_pt"
    item_attributes = {"brand": "Montepio", "brand_wikidata": "Q1946091"}
    start_urls = ["https://www.bancomontepio.pt/onde-estamos"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for card in response.xpath('//*[@id="map__tabpanel--atms"]//div[@data-latitude]'):
            item = self.parse_card(card)  # standalone ATM keeps the host-venue title as name
            apply_category(Categories.ATM, item)
            yield item

        # balcoes + business/social centres are branches; "atms" is handled above and the foreign
        # "banco-montepio-no-mundo" offices are out of scope for a PT spider.
        for section in ("balcoes", "centros-economia-social", "centros-empresas"):
            for card in response.xpath('//*[@id="map__tabpanel--{}"]//div[@data-latitude]'.format(section)):
                item = self.parse_card(card)
                item["branch"] = item.pop("name")  # NSI supplies name=Montepio
                if phone := card.xpath('.//a[starts-with(@href, "tel:")]/@href').get():
                    item["phone"] = unquote(phone.removeprefix("tel:"))  # href is percent-encoded
                if email := card.xpath('.//a[starts-with(@href, "mailto:")]/@href').get():
                    item["email"] = email.removeprefix("mailto:")
                item["opening_hours"] = self.parse_hours(card)
                services = " ".join(card.xpath(".//text()").getall())
                apply_yes_no(Extras.ATM, item, "ATM" in services or "Chave24" in services)
                apply_category(Categories.BANK, item)
                yield item

    def parse_card(self, card: Any) -> Feature:
        lat = card.xpath("@data-latitude").get()
        lon = card.xpath("@data-longitude").get()
        name = card.xpath('normalize-space(.//*[contains(@class, "detailed-card__title")])').get()
        item = Feature(ref="/".join([lat, lon, name or ""]), lat=lat, lon=lon, name=name)
        # Address is two lines: "<street, number>" then "<postcode> <city>" (Portuguese NNNN-NNN).
        address = [
            t.strip()
            for t in card.xpath('.//*[contains(@class, "detailed-card__address")]//text()').getall()
            if t.strip()
        ]
        if len(address) >= 2:
            item["street_address"] = address[0]
            if match := POSTCODE.match(address[1]):
                item["postcode"], item["city"] = match.groups()
            else:
                item["city"] = address[1]
        elif address:
            item["addr_full"] = address[0]
        return item

    @staticmethod
    def parse_hours(card: Any) -> str | None:
        # "Horário Dias úteis: 08h30 - 15h00" (weekdays); a trailing "por agendamento" (by appointment)
        # range is ignored by taking the first time range only.
        text = " ".join(card.xpath('.//*[contains(@class, "detailed-card__schedule")]//text()').getall())
        if not (match := TIME_RANGE.search(text)):
            return None
        try:
            hours = OpeningHours()
            hours.add_days_range(DAYS_WEEKDAY, "{}:{}".format(match[1], match[2]), "{}:{}".format(match[3], match[4]))
            return hours.as_opening_hours()
        except ValueError:
            return None
