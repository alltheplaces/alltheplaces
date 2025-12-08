import json
from typing import Any

from scrapy import FormRequest, Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature
from locations.structured_data_spider import extract_email


class BigmatESPTSpider(Spider):
    name = "bigmat_es_pt"
    item_attributes = {"brand": "BigMat", "brand_wikidata": "Q101851862"}
    start_urls = ["https://www.bigmat.es/es/t/almacenes-de-construccion"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for area in response.xpath("//*[@data-locationname][@data-locationname]"):
            yield FormRequest(
                url="https://www.bigmat.es/es/home/t",
                formdata={
                    "province": area.xpath("@data-locationname").get(),
                    "idCountry": area.xpath("@data-idcountry").get(),
                    "CP": "",
                },
                callback=self.parse_area,
            )

    def parse_area(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.json()):
            item = Feature()
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]

            sel = Selector(text=location["infoShop"])
            extract_email(item, sel)
            item["ref"] = item["website"] = response.urljoin(
                sel.xpath('//a[contains(@href, "almacenes-de-construccion")]/@href').get()
            )
            yield item
