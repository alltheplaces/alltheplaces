from typing import Iterable

from scrapy import Request, Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HumanImmobilierFRSpider(StructuredDataSpider):
    name = "human_immobilier_fr"
    item_attributes = {"brand": "Human Immobilier", "brand_wikidata": "Q102352527"}
    start_urls = ["https://www.human-immobilier.fr/agences-immobilieres"]
    wanted_types = ["RealEstateAgent"]
    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response: Response, **kwargs) -> Iterable[Feature | Request]:
        for point in response.xpath('//div[@class="point-map"]'):
            popup = Selector(text=point.xpath('./input[@class="title"]/@value').get())
            path = popup.xpath("//a/@href").get()
            if path == "/louer/siege":
                continue
            item = Feature()
            item["ref"] = path.strip("/")
            item["website"] = response.urljoin(path)
            item["lat"] = point.xpath('./input[@class="latitude"]/@value').get().replace(",", ".")
            item["lon"] = point.xpath('./input[@class="longitude"]/@value').get().replace(",", ".")
            apply_category(Categories.OFFICE_ESTATE_AGENT, item)
            if path.startswith("/louer/"):
                # Rental management offices have no agency structured data on their pages
                item["branch"] = popup.xpath('//*[@class="infobox__agence-name"]/text()').get()
                item["street_address"], item["addr_full"] = popup.xpath('//*[@class="i-adresse"]/text()').getall()
                item["postcode"], item["city"] = item.pop("addr_full").split(" ", 1)
                yield item
            else:
                yield Request(item["website"], callback=self.parse_sd, meta={"point": item})

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.update(response.meta["point"])
        item["branch"] = item.pop("name")
        yield item
