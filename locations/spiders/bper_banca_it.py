from typing import Any, AsyncIterator, Optional

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BperBancaITSpider(Spider):
    name = "bper_banca_it"
    BRANDS = {
        "5387": ("BPER Banca", "Q806167"),
        "3084": ("Banca Cesare Ponti", "Q3633696"),
        "1015": ("Banco di Sardegna", "Q806205"),
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.bper.it/o/bper-api/subsidiary/search/categories",
            data={"abiCode": "", "groupId": "2084926082", "categoryIds": []},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json()["payload"]["subsidiaryListGeoloc"]:
            bank.update(bank.pop("contacts"))
            bank["street_address"] = bank.pop("address")
            item = DictParser.parse(bank)
            item["name"] = bank["bankName"]
            item["city"] = bank["cityDescription"]
            item["website"] = response.urljoin(bank["linkSubsidiaryCard"])
            item["opening_hours"] = self.parse_hours(bank.get("timetables"))
            item["brand"], item["brand_wikidata"] = self.BRANDS.get(bank.get("bankCode"), (bank.get("bankName"), None))

            services = [service["title"] for service in bank.get("services")]
            apply_yes_no(Extras.ATM, item, any(service.startswith("ATM ") for service in services))

            apply_category(Categories.BANK, item)

            yield item

    def parse_hours(self, hours: dict) -> Optional[OpeningHours]:
        try:
            if hours:
                oh = OpeningHours()
                for day in DAYS_FULL:
                    for range in [f"open{day}Morning", f"open{day}Afternoon"]:
                        times = hours.get(range)
                        if " " not in times:
                            continue
                        oh.add_range(
                            day,
                            times.split(" ")[0],
                            times.split(" ")[1],
                            time_format="%H.%M",
                        )
                return oh
        except:
            self.logger.error(f"Failed to parse opening hours: {hours}")
        return None
