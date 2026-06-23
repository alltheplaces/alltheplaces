from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class ZiraatBankasiTRSpider(Spider):
    name = "ziraat_bankasi_tr"
    item_attributes = {"brand": "Ziraat Bankası", "brand_wikidata": "Q696003"}

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            "https://www.ziraatbank.com.tr/tr/bize-ulasin/sube-ve-atmler",
            callback=self.parse_finder,
        )

    def parse_finder(self, response: Response) -> Any:
        states = {
            option.attrib["value"]: option.xpath("normalize-space()").get()
            for option in response.xpath('//*[@id="ddlCity"]/option')
            if option.attrib.get("value") and option.attrib["value"] != "0"
        }

        # Detail endpoints exist, but require one request per POI; with the project download delay that is a multi-hour crawl.
        for location_type, category, list_method, width in [
            ("branch", Categories.BANK, "GetAllSubeText", 8),
            ("atm", Categories.ATM, "GetAllAtmText", 7),
        ]:
            yield JsonRequest(
                url=f"https://www.ziraatbank.com.tr/tr/_layouts/15/Ziraat/SubeATM/Ajax.aspx/{list_method}",
                data={},
                headers={
                    "Referer": "https://www.ziraatbank.com.tr/tr/bize-ulasin/sube-ve-atmler",
                    "X-Requested-With": "XMLHttpRequest",
                },
                callback=self.parse_location_list,
                cb_kwargs={"location_type": location_type, "category": category, "states": states, "width": width},
            )

    def parse_location_list(
        self,
        response: Response,
        location_type: str,
        category: dict[str, str],
        states: dict[str, str],
        width: int,
    ) -> Any:
        parts = response.json()["d"]["Data"].split("|")

        if len(parts) % width != 0:
            self.logger.error("Unexpected {} payload width from {}".format(location_type, response.url))
            return

        for index in range(0, len(parts), width):
            fields = parts[index : index + width]
            state = states.get(fields[-2])
            if not state:
                self.crawler.stats.inc_value(f"atp/{self.name}/skipped_unknown_state")
                continue

            # Marker feeds are pipe-delimited and expose id, coordinates, service flags, province id, and district id.
            item = Feature(
                ref=f"{location_type}-{fields[0]}",
                lat=fields[1].replace(",", "."),
                lon=fields[2].replace(",", "."),
                state=state,
            )
            apply_category(category, item)

            if category == Categories.BANK:
                apply_yes_no(Extras.WHEELCHAIR, item, fields[4] == "1")
            else:
                apply_yes_no(Extras.CASH_IN, item, fields[3] == "2")
                apply_yes_no(Extras.CASH_OUT, item, fields[3] == "1")
                apply_yes_no(Extras.WHEELCHAIR, item, fields[4] == "1")

            yield item
