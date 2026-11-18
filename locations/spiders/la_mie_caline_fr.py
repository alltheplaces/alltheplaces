import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours
from locations.items import Feature


class LaMieCalineFRSpider(Spider):
    name = "la_mie_caline_fr"
    item_attributes = {"brand": "La Mie Câline", "brand_wikidata": "Q3210704"}
    ajax_url = "https://www.lamiecaline.com/wp-admin/admin-ajax.php"

    async def start(self) -> AsyncIterator[Any]:
        yield Request(f"{self.ajax_url}?action=get_franchise_markers", callback=self.parse_markers)

    def parse_markers(self, response: Response, **kwargs: Any) -> Any:
        for marker in response.json():
            yield Request(
                f"{self.ajax_url}?action=get_unique_franchise_listing&franchise={marker['ID']}",
                cb_kwargs={"marker": marker},
            )

    def parse(self, response: Response, marker: dict, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = marker["ID"]
        item["branch"] = marker["name"]
        if marker["lat"] and marker["lng"]:
            item["lat"] = marker["lat"]
            item["lon"] = marker["lng"]

        headings = response.xpath('//h2[@class="elementor-heading-title elementor-size-default"]/a')
        item["website"] = headings.xpath("@href").get()
        if len(headings) > 1:
            item["addr_full"] = headings[1].xpath("normalize-space()").get()
        item["phone"] = response.xpath(
            '//a[starts-with(@href, "tel:")]/span[@class="elementor-icon-list-text"]/text()'
        ).get()

        item["opening_hours"] = OpeningHours()
        for day in response.xpath('//div[contains(concat(" ", @class, " "), " day ")]'):
            day_name = DAYS_FR.get(day.xpath('./div[@class="label"]/text()').get("").strip())
            hours = day.xpath('./div[@class="hours"]/text()').get("").strip()
            if hours.lower() in CLOSED_FR:
                item["opening_hours"].set_closed(day_name)
            for open_time, close_time in re.findall(r"(\d{1,2}h\d{2}) à (\d{1,2}h\d{2})", hours):
                item["opening_hours"].add_range(day_name, open_time, close_time, "%Hh%M")

        apply_category(Categories.SHOP_BAKERY, item)
        yield item
