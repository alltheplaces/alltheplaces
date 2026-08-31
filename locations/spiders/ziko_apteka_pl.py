import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ZikoAptekaPLSpider(JSONBlobSpider):
    name = "ziko_apteka_pl"
    item_attributes = {"brand": "Ziko Apteka", "brand_wikidata": "Q63432892"}
    allowed_domains = ["zikoapteka.pl"]
    start_urls = ["https://zikoapteka.pl/wp-admin/admin-ajax.php?action=get_pharmacies"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            # The endpoint returns 403 unless a same-site Referer is supplied.
            yield JsonRequest(url=url, headers={"Referer": "https://zikoapteka.pl/apteki"})

    def pre_process_data(self, location: dict) -> None:
        # Some records use a comma as the decimal separator in coordinates.
        for key in ("lat", "lng"):
            if isinstance(location.get(key), str):
                location[key] = location[key].replace(",", ".")

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["ref"] = location["mypostid"]
        item["city"] = location["city_name"][0]
        item.pop("state", None)
        if location.get("link"):
            item["website"] = "https://zikoapteka.pl/apteki" + location["link"] + "/"
        item["opening_hours"] = OpeningHours()
        # drop the qualifier so "niedziela" is read as Sunday.
        item["opening_hours"].add_ranges_from_string(
            re.sub(
                r"\s+",
                " ",
                re.sub(r"niehandlowa|handlowa", "", location["mp_pharmacy_hours"].replace("<br>", " ")).replace(
                    ".", ""
                ),
            ),
            days=DAYS_PL,
        )
        item["street_address"] = item.pop("addr_full", None)
        apply_category(Categories.PHARMACY, item)
        yield item
