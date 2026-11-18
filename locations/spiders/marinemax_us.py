from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MarinemaxUSSpider(Spider):
    name = "marinemax_us"
    item_attributes = {"brand": "MarineMax", "brand_wikidata": "Q119140995"}
    start_urls = ["https://www.marinemax.com/pages/locations"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//*[@data-location-index]"):
            item = Feature()
            item["website"] = response.urljoin(location.xpath('.//a[@class="location-card__title-link"]/@href').get())
            item["ref"] = item["website"].rsplit("/", 1)[-1]
            item["branch"] = (
                location.xpath('normalize-space(.//a[@class="location-card__title-link"])')
                .get()
                .removeprefix("MarineMax ")
            )
            item["addr_full"] = merge_address_lines(
                location.xpath('.//p[@class="location-card__address"]/text()').getall()
            )
            item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/@href').get()
            extract_google_position(item, location)
            yield Request(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Any:
        item["opening_hours"] = OpeningHours()
        for day in response.xpath('(//table[@class="location-detail-hours-modal__table"])[1]//tr'):
            item["opening_hours"].add_ranges_from_string(day.xpath("normalize-space()").get())
        yield item
