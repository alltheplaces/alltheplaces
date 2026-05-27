from typing import Any

from chompjs import chompjs
from scrapy import Spider, Selector
from scrapy.http import Response

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class LaPizzaDeNicoFRSpider(Spider):
    name = "la_pizza_de_nico_fr"
    item_attributes = {"brand": "La Pizza de Nico", "brand_wikidata": "Q139917217"}
    start_urls = ["https://lapizzadenico.com/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath("//script[contains(text(), 'restoLocation')]/text()").get()
        ):
            item = Feature()
            item["name"], item["lat"], item["lon"], _, sel_text = location
            item["branch"] = item.pop("name").removeprefix("La Pizza de Nico ")

            sel = Selector(text=sel_text)
            item["image"] = (
                sel.xpath('//div[@class="mapThumbnail"]/@style')
                .get()
                .removeprefix("background-image:url(")
                .removesuffix(");")
            )
            item["ref"] = item["website"] = sel.xpath("//a/@href").get()
            item["extras"]["website:menu"] = sel.xpath('//a[contains(text(), "menu")]/@href').get()
            extract_phone(item, sel)

            apply_category(Categories.RESTAURANT, item)

            yield item
