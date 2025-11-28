import base64
import json
import re
from typing import AsyncIterator, Iterable

from scrapy.http import FormRequest, Request, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, DAYS_IT, OpeningHours
from locations.items import Feature


class EathappySpider(Spider):
    name = "eathappy"
    item_attributes = {"brand": "Eat Happy", "brand_wikidata": "Q125578025"}
    countries = {
        "AT": {
            "url": "https://www.eathappy.at/standorte/",
            "day_names": DAYS_DE,
        },
        "DE": {
            "url": "https://www.eathappy.de/standorte/",
            "day_names": DAYS_DE,
        },
        "IT": {
            "url": "https://www.eathappy.it/dove-siamo/",
            "day_names": DAYS_IT,
        },
    }
    ajax_post_id = 1086

    async def start(self) -> AsyncIterator[Request]:
        # Need to get the data from two URLs: The HTML page contains a JavaScript block with the IDs and coordinates
        for country, country_definition in self.countries.items():
            yield Request(url=country_definition["url"], callback=self.parse, cb_kwargs={"country": country})

    def parse(self, response: Response, country: str = "DE", **kwargs) -> Iterable[Feature]:
        re_extract = r"\s*var locations\s*=\s*(\[.*\]);\s*"
        locations_javascript = response.xpath('//div[@id="map"]/following-sibling::script/text()').re(re_extract)
        if locations_javascript:
            locations_javascript = locations_javascript[0]
        else:
            locations_base64 = response.xpath('//div[@id="map"]/following-sibling::script/@src').get()
            locations_javascript = str(base64.standard_b64decode(locations_base64.split(",")[-1]), "utf-8")
            locations_javascript = re.sub(re_extract, r"\1", locations_javascript, re.MULTILINE)
        locations_array = json.loads(locations_javascript)
        shop_coordinates = {shop["id"]: shop for shop in locations_array}
        # This is the second URL and contains the name, address and opening hours. The data is merged with the first URL
        # via the ID
        yield FormRequest(
            url=response.urljoin("/wp-admin/admin-ajax.php"),
            formdata={"action": "ajax_load_map_locations", "post_id": str(self.ajax_post_id)},
            meta={"shops": shop_coordinates},
            callback=self.parse_shops,
            cb_kwargs={"country": country},
        )

    def parse_shops(self, response: Response, country: str = "DE") -> Iterable[Feature]:
        shop_coordinates = response.meta["shops"]
        for location in response.xpath('/html/body/div[@class="map-sidebar-location"]'):
            item = Feature()
            shop_id = int(location.attrib["data-location-id"])
            item["ref"] = shop_id
            div = location.xpath('div[@class="desc"]')
            item["located_in"] = div.xpath("h6/text()").get()
            item["addr_full"] = div.xpath("h6/following-sibling::p/text()").get()
            item["country"] = country
            opening_hours = OpeningHours()
            for row in div.xpath('div/div[@class="opening-hours-table"]/div[@class="opening-hours-row"]'):
                label = row.xpath('div[@class="opening-hours-label"]/text()').get().replace(":", "")
                day = self.countries[country]["day_names"][label.title()]
                period = row.xpath('normalize-space(div[@class="opening-hours-value"]/text())').get()
                if "-" in period:
                    opening_time, closing_time = period.split("-")
                    opening_hours.add_range(day, opening_time, closing_time, "%H:%M")
            item["opening_hours"] = opening_hours
            item["lon"] = shop_coordinates[shop_id]["lng"]
            item["lat"] = shop_coordinates[shop_id]["lat"]

            apply_category(Categories.FAST_FOOD, item)

            yield item
