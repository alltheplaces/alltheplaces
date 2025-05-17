from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories,apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

TEXACO_SHARED_ATTRIBUTES = {"brand": "Texaco", "brand_wikidata": "Q775060"}


class TexacoCOSpider(Spider):
    name = "texaco_co"
    item_attributes = TEXACO_SHARED_ATTRIBUTES
    allowed_domains = ["www.texacocontechron.com"]
    start_urls = ["https://www.texacocontechron.com/co/estaciones/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for station in response.xpath("//div[@data-station-id]"):
            properties = {
                "branch": station.xpath('./@data-station-id').get(),
                "lat": station.xpath('./div[2]/button[1]/@onclick').get().split("selectStation('", 1)[1].split("'", 1)[0],
                "lon": station.xpath('./div[2]/button[1]/@onclick').get().split("', '", 1)[1].split("'", 1)[0],
                "addr_full": merge_address_lines(station.xpath('./div[1]/p[1]//text()').getall()),
                "city": station.xpath('./@data-city').get(),
                "state": station.xpath('./@data-province').get(),
            }
            apply_category(Categories.FUEL_STATION, properties)
            yield Feature(**properties)
