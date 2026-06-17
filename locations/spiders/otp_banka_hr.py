import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_HR, OpeningHours
from locations.items import Feature


class OtpBankaHRSpider(Spider):
    name = "otp_banka_hr"
    item_attributes = {"brand": "OTP banka", "brand_wikidata": "Q31198593"}

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            url="https://www.otpbanka.hr/poslovnice/print",
            cb_kwargs={"location_type": "branch"},
        )
        yield Request(
            url="https://www.otpbanka.hr/atms/print",
            cb_kwargs={"location_type": "atm"},
        )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for row in response.xpath('//table[contains(@class, "views-table")]//tbody/tr'):
            item = self.parse_location(row, response)

            if location_type == "branch":
                self.parse_hours(item, row)
                apply_yes_no(
                    Extras.WHEELCHAIR,
                    item,
                    row.xpath('normalize-space(.//*[contains(@class, "views-field-field-pristup-za-invalide")])')
                    .get("")
                    .strip()
                    == "Pristup za invalide",
                    False,
                )
                apply_category(Categories.BANK, item)
            elif location_type == "atm":
                apply_yes_no(
                    Extras.CASH_IN,
                    item,
                    row.xpath('normalize-space(.//*[contains(@class, "views-field-field-vrsta-bankomata-tablica")])')
                    .get("")
                    .strip()
                    == "Uplatno-isplatni bankomat",
                    False,
                )
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item

    def parse_hours(self, item: Feature, row: Any) -> None:
        rules = row.xpath(
            './/*[contains(@class, "views-field-field-radno-vrijeme")]'
            '//*[contains(concat(" ", normalize-space(@class), " "), " oh-display ")]'
        )
        if not rules:
            return

        days_hr = DAYS_HR | {
            "Pon": "Mo",
            "Uto": "Tu",
            "Sri": "We",
            "\u010cet": "Th",
            "Pet": "Fr",
            "Sub": "Sa",
            "Ned": "Su",
        }
        oh = OpeningHours()
        try:
            for rule in rules:
                day = days_hr[
                    rule.xpath(
                        'normalize-space(.//*[contains(concat(" ", normalize-space(@class), " "), " oh-display-label ")])'
                    )
                    .get("")
                    .rstrip(":")
                    .strip()
                ]
                hours = (
                    rule.xpath(
                        'normalize-space(.//*[contains(concat(" ", normalize-space(@class), " "), " oh-display-times ")])'
                    )
                    .get("")
                    .strip()
                )
                if hours == "Zatvoreno":
                    oh.set_closed(day)
                elif "-" in hours:
                    oh.add_range(day, *hours.split("-", 1))
                else:
                    raise ValueError("Unexpected opening hours value: {}".format(hours))
            item["opening_hours"] = oh
        except Exception:
            self.logger.warning("Failed to parse hours for {}".format(item.get("ref")))

    @staticmethod
    def parse_location(row: Any, response: Response) -> Feature:
        # Source rows are HTML tables rather than JSON, so DictParser is not applicable.
        item = Feature()

        if href := row.xpath('.//a[contains(@href, "/offices-atms/")]/@href').get():
            if match := re.search(r"/offices-atms/(\d+)", href):
                item["ref"] = match.group(1)
            item["website"] = response.urljoin(href)

        if branch := row.xpath("normalize-space(./td[2])").get():
            item["branch"] = branch.removeprefix("Poslovnica ").strip()
        item["street_address"] = row.xpath('normalize-space(.//*[contains(@class, "street-address")])').get()
        item["city"] = row.xpath('normalize-space(.//*[contains(@class, "views-field-city")]//a)').get()
        if phone := row.xpath(
            'normalize-space(.//*[contains(@class, "views-field-field-telefon")]//a[contains(@href, "tel:")])'
        ).get():
            item["phone"] = phone

        if match := re.match(
            r"(?P<lat>-?\d+(?:\.\d+)?)\s*,\s*(?P<lon>-?\d+(?:\.\d+)?)",
            row.xpath('normalize-space(.//*[contains(@class, "views-field-coordinates")]//a)').get(""),
        ):
            item["lat"] = match.group("lat")
            item["lon"] = match.group("lon")

        return item
