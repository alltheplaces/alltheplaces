import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ"}


class VillaverdeSpider(Spider):
    name = "villaverde"
    item_attributes = {"brand_wikidata": "Q89346546"}
    start_urls = ["https://www.villaverde.fr/nos-magasins"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.css(".custom-magasin"):
            item = Feature()
            url = store.css("a::attr(href)").get()
            item["ref"] = url.strip("/").rsplit("/", 1)[-1]
            item["branch"] = " ".join(store.attrib["data-name"].removeprefix("VillaVerde ").split())
            # The list's address attribute ends with a stray "</div>"
            address = " ".join(store.attrib["data-adresse"].removesuffix("</div>").split())
            item["street_address"], item["postcode"], item["city"] = re.match(
                r"(.*?)\s*(\d{5})\s+(.+)", address
            ).groups()
            item["country"] = OVERSEAS_COUNTRIES.get(item["postcode"][:3], "FR")
            yield response.follow(url, callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: Feature) -> Any:
        item["website"] = response.url
        item["phone"] = response.css('.o_vv_store_coords a[href^="tel:"] span::text').get()

        # Newer store pages and older hand built pages use different hours tables
        table = response.css(".o_vv_store_hours_container table, table.horaires-table")[:1]
        if table:
            oh = OpeningHours()
            for row in table.css("tr"):
                day, *times = [" ".join(cell.css("::text").getall()) for cell in row.css("td")]
                if not (day := sanitise_day(day.strip(" *"), DAYS_FR)):
                    continue
                times = " ".join(times)
                if "Fermé" in times:
                    oh.set_closed(day)
                for start, end in re.findall(r"(\d{1,2}:\d{2})\s*[-/]\s*(\d{1,2}:\d{2})", times):
                    oh.add_range(day, start, end)
            item["opening_hours"] = oh

        yield item
