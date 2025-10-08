from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MitsubishiAfricaSpider(CrawlSpider):
    name = "mitsubishi_africa"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = [
        "https://www.mitsubishi-motors.ci/fr/concessions/",
        "https://mitsubishimotors.cfaomotors-gabon.com/fr/concessions/",
        "https://www.mitsubishi-motors.com.gh/en/concessions",
        "https://www.mitsubishi-motors.mg/fr/concessions/",
        "https://www.mitsubishi-motors-liberia.com/en/concessions",
        "https://www.mitsubishi-motors.bj/fr/concession/mitsubishi-benin-cfao-motors",
        "https://www.mitsubishimotors-centrafrique.com/fr/concession/mitsubishi-centrafrique-cfao-motors",
        "https://mitsubishimotors.cfaomotors-mauritanie.com/fr/concessions/",
        "https://www.mitsubishi-motors.com.ng/en/concessions/",
        "https://www.mitsubishi-motors.tg/fr/concession/mitsubishi-togo-cfao-motors",
    ]
    rules = [Rule(LinkExtractor(restrict_xpaths='//*[@class="concessions"]'), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@id = "dealership"]//*[@class="content-heading"]//text()').get()
        item["street_address"] = response.xpath('//*[@class="location-info"]/div[1]/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('//*[@class="location-info"]/div[2]/text()').get()]
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        lat_lon = chompjs.parse_js_object(response.xpath('//*[contains(text(),"map_markers")]/text()').get())
        item["lat"] = lat_lon[0][1]
        item["lon"] = lat_lon[0][2]
        apply_category(Categories.SHOP_CAR, item)
        yield item
