import re
import urllib.parse
from datetime import date
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KadoilTRSpider(Spider):
    name = "kadoil_tr"
    item_attributes = {"brand": "Kadoil", "brand_wikidata": "Q126901221"}
    no_refs = True

    async def start(self) -> AsyncIterator[Any]:
        yield Request("https://admin.kadoil.com/station-lists/map", callback=self.parse_provinces)

    def parse_provinces(self, response: Response, **kwargs: Any) -> Any:
        today = date.today().isoformat()
        for province in response.xpath('//select[@id="selectProvince"]/option[@value!=""]/@value').getall():
            yield Request(
                url="https://admin.kadoil.com/api/station-lists",
                method="POST",
                body=urllib.parse.urlencode({"date": today, "province": province}),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                callback=self.parse_stations,
            )

    def parse_stations(self, response: Response, **kwargs: Any) -> Any:
        for row in response.xpath("//table//tr[td]"):
            map_href = row.xpath('.//a[contains(@href, "maps")]/@href').get("")
            coords = re.search(r"//(-?[\d.]+),(-?[\d.]+)/", map_href)
            if not coords:
                continue
            cells = row.xpath("td")
            address = cells[3].xpath("normalize-space(.)").get("")
            item = Feature()
            item["lat"] = coords.group(1)
            item["lon"] = coords.group(2)
            item["name"] = cells[2].xpath("normalize-space(.)").get("")
            item["addr_full"] = address
            item["state"] = cells[0].xpath("normalize-space(.)").get("")
            item["city"] = cells[1].xpath("normalize-space(.)").get("")
            apply_category(Categories.FUEL_STATION, item)
            yield item
