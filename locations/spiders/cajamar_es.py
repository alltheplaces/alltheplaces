from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CajamarESSpider(Spider):
    name = "cajamar_es"
    item_attributes = {"brand": "Cajamar", "brand_wikidata": "Q8254971"}
    start_urls = [
        "https://www.grupocooperativocajamar.es/frontend/kml/cajerostodo.kml",
        "https://www.grupocooperativocajamar.es/frontend/kml/oficinastodo.kml",
    ]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.xpath("/kml/Document/Placemark"):
            item = Feature()
            item["lat"] = location.xpath("./lookAt/latitude/text()").get()
            item["lon"] = location.xpath("./lookAt/longitude/text()").get()

            item["website"] = (
                Selector(text=location.xpath("./description/text()").get()).xpath(".//a/@href").getall()[-1]
            )

            if "oficinastodo.kml" in response.url:
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)

            yield item
