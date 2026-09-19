from typing import Any, AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

ALLOWED_RESOURCE_TYPES = ["document", "script", "fetch"]


class SdekSpider(CamoufoxSpider):
    name = "sdek"
    allowed_domains = ["www.cdek.ru"]
    item_attributes = {"brand": "СДЭК", "brand_wikidata": "Q28665980"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ALLOWED_RESOURCE_TYPES
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.cdek.ru/ru/offices/",
            meta={
                "camoufox_page_methods": [
                    # Navigation returns while the challenge is still running, and
                    # fetching before it has reloaded the page gets an HTTP 418.
                    PageMethod("wait_for_selector", "js-challenge-loader", state="detached", timeout=60000),
                    PageMethod(
                        "evaluate",
                        """async () => {
                            // The API silently falls back to a page size of 25 for any limit above 100.
                            const PAGE_SIZE = 100;
                            const url = (page) => "/api-site/website/office/?locale=ru"
                                + "&coords[startLat]=-90&coords[startLong]=-180&coords[endLat]=90&coords[endLong]=180"
                                + "&limit=" + PAGE_SIZE + "&page=" + page;
                            const fetchPage = async (page) => {
                                const response = await fetch(url(page), {headers: {"Accept": "application/json"}});
                                if (!response.ok) throw new Error(url(page) + " returned HTTP " + response.status);
                                return (await response.json()).data;
                            };

                            const firstPage = await fetchPage(1);
                            const offices = [...firstPage.data];
                            const pages = Math.ceil(firstPage.amount / PAGE_SIZE);
                            for (let page = 2; page <= pages; page++) {
                                await new Promise((resolve) => setTimeout(resolve, 1000));
                                offices.push(...(await fetchPage(page)).data);
                            }
                            return offices;
                        }""",
                    ),
                ]
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Index 1 is the fetch loop, index 0 is the challenge wait above.
        for poi in response.meta["camoufox_page_methods"][1].result:
            item = DictParser.parse(poi)
            item["street_address"] = item.pop("addr_full")
            item["ref"] = poi.get("code")
            item["website"] = f'https://www.cdek.ru/ru/offices/view/{item["ref"]}/'
            item["lat"] = poi.get("geoLatitude")
            item["lon"] = poi.get("geoLongitude")

            category = poi.get("type")
            if category == "PVZ":
                apply_category(Categories.POST_OFFICE, item)
            elif category == "POSTAMAT":
                apply_category(Categories.PARCEL_LOCKER, item)
                apply_yes_no("parcel_mail_in", item, poi.get("isReception"))
                apply_yes_no("parcel_pickup", item, poi.get("isHangout"))
            self.parse_hours(item, poi)
            item["extras"]["brand:en"] = "SDEK"
            yield item

    def parse_hours(self, item: Feature, poi: dict) -> None:
        if hours := poi.get("worktimes"):
            try:
                oh = OpeningHours()
                for hour in hours:
                    oh.add_range(
                        day=DAYS[hour["day"] - 1],
                        open_time=hour["startTime"],
                        close_time=hour["stopTime"],
                        time_format="%H:%M:%S",
                    )
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {hours}, {e}")
