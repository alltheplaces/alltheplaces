# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class TangerOutletSpider(scrapy.Spider):
    name = "tanger_outlet"
    allowed_domains = ["www.tangeroutlet.com"]
    download_delay = 0.1
    start_urls = ("https://www.tangeroutlet.com/locations",)

    def parse(self, response):
        storeselector = response.xpath(
            './/div[@id="centerIndexList"]/div[@class="row"]/div'
        )
        for i in range(len(storeselector)):
            properties = {
                "ref": "https://www.tangeroutlet.com/"
                + storeselector[i].xpath(".//@data-webmoniker").extract_first()
                + "/location",
                "brand": "Tanger Outlet",
                "addr_full": storeselector[i]
                .xpath('.//span[@class="address"]/text()')
                .extract_first()
                .strip(),
                "city": storeselector[i].xpath(".//@data-city").extract_first(),
                "state": storeselector[i]
                .xpath('.//span[@class="address-info"]/text()')
                .extract_first()
                .split()[-2],
                "postcode": storeselector[i]
                .xpath('.//span[@class="address-info"]/text()')
                .extract_first()
                .split()[-1],
                "phone": storeselector[i]
                .xpath('.//span[@class="phone"]/text()')
                .extract_first(),
                "opening_hours": storeselector[i]
                .xpath('.//span[@class="todays-hours"]/span[@class="break"]/text()')
                .extract_first(),
                "website": "https://www.tangeroutlet.com/"
                + storeselector[i].xpath(".//@data-webmoniker").extract_first()
                + "/location",
                "lat": storeselector[i].xpath(".//@data-latitude").extract_first(),
                "lon": storeselector[i].xpath(".//@data-longitude").extract_first(),
            }
            yield GeojsonPointItem(**properties)
