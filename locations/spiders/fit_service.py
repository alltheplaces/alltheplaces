import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

SERVICES_MAPPING = {
    "автомойка": Extras.CAR_WASH,
    "автосервис": Extras.CAR_REPAIR,
    "диагностика": None,
    "доп. оборудование": None,
    "шиномонтаж": Extras.TYRE_SERVICES,
}


class FitServiceSpider(scrapy.Spider):
    """At a time of writing has locations in RU and KZ."""

    name = "fit_service"
    allowed_domains = ["fitauto.ru"]
    item_attributes = {"brand": "Fit Service", "brand_wikidata": "Q129632037"}
    start_urls = ["https://fitauto.ru/contacts/"]
    requires_proxy = True

    def parse(self, response: Response):
        for poi in response.xpath("//e-page--contacts--item"):
            item = Feature()
            item["ref"] = poi.xpath("@a-id").get()
            item["lat"] = poi.xpath("@a-lat").get()
            item["lon"] = poi.xpath("@a-lng").get()
            item["city"] = poi.xpath("h2/span/span/text()").get()
            street_address = poi.xpath("h2/span/text()").getall()
            street_address = ", ".join([a for a in street_address if a != ", "])
            item["street_address"] = street_address
            item["phone"] = poi.xpath('a[@slot="phone"]/text()').get()
            services = poi.xpath('ul[@slot="services"]/li/text()').getall()
            for service in filter(None, services):
                service = service.lower().strip()
                if match := SERVICES_MAPPING.get(service):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/service/failed/{service}")
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
