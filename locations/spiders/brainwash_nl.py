from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_NL, DAYS_NL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BrainwashNLSpider(Spider):
    name = "brainwash_nl"
    item_attributes = {"brand": "BrainWash", "brand_wikidata": "Q114905133"}
    allowed_domains = ["www.brainwash-kappers.nl"]
    start_urls = ["https://www.brainwash-kappers.nl/salons/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for salon in response.xpath('//div[@class="salon-item"]'):
            properties = {
                "ref": salon.xpath("./@data-marker-id").get(),
                "branch": salon.xpath(".//h4/text()").get().removeprefix("Brainwash ").removeprefix("BrainWash "),
                "lat": salon.xpath("./@data-marker-lat").get(),
                "lon": salon.xpath("./@data-marker-lng").get(),
                "addr_full": merge_address_lines(
                    salon.xpath('.//div[@class="info-window"]/p/text()[position()<=2]').getall()
                ),
                "phone": salon.xpath('.//div[@class="info-window"]/p/text()[3]').get(),
                "website": salon.xpath('.//div[@class="info-window"]/a/@href').get(),
                "opening_hours": OpeningHours(),
            }

            hours_string = " ".join(salon.xpath(".//div[@data-open-hours-table]//text()").getall())
            properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_NL, closed=CLOSED_NL)

            apply_category(Categories.SHOP_HAIRDRESSER, properties)

            yield Feature(**properties)
