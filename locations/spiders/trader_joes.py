# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class TraderJoesSpider(scrapy.Spider):
    name = "trader_joes"
    item_attributes = {"brand": "Trader Joe's"}
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = (
        'https://hosted.where2getit.com/traderjoes/ajax?&xml_request=<request><appkey>8559C922-54E3-11E7-8321-40B4F48ECC77</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><limit>3000</limit><geolocs><geoloc><addressline>53209</addressline><longitude></longitude><latitude></latitude><country></country></geoloc></geolocs><searchradius>3000</searchradius><where></where></formdata></request>',
    )

    def parse(self, response):
        data = response.xpath("//poi")

        for store in data:
            properties = {
                "ref": str(store.xpath("clientkey/text()").extract_first()),
                "name": store.xpath("name/text()").extract_first(),
                "addr_full": store.xpath("address1/text()").extract_first(),
                "city": store.xpath("city/text()").extract_first(),
                "state": store.xpath("state/text()").extract_first(),
                "postcode": store.xpath("postalcode/text()").extract_first(),
                "country": store.xpath("country/text()").extract_first(),
            }

            phone = store.xpath("phone/text()")
            if phone:
                properties["phone"] = phone.extract_first()

            properties["lon"] = store.xpath("longitude/text()").extract_first()
            properties["lat"] = store.xpath("latitude/text()").extract_first()

            yield GeojsonPointItem(**properties)
