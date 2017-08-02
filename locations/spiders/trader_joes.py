# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class TraderJoesSpider(scrapy.Spider):
    name = "trader_joes"
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = (
        'https://hosted.where2getit.com/traderjoes/ajax?&xml_request=<request><appkey>8559C922-54E3-11E7-8321-40B4F48ECC77</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><limit>3000</limit><geolocs><geoloc><addressline>55114</addressline><longitude></longitude><latitude></latitude><country></country></geoloc></geolocs><searchradius>3000</searchradius><where></where></formdata></request>',
    )

    def address(self, store):
        addr_tags = {
            "addr:full": store.xpath('address1/text()')[0].extract(),
            "addr:city": store.xpath('city/text()')[0].extract(),
            "addr:state": store.xpath('state/text()')[0].extract(),
            "addr:postcode": store.xpath('postalcode/text()')[0].extract(),
            "addr:country": store.xpath('country/text()')[0].extract(),
        }

        return addr_tags

    def parse(self, response):
        data = response.xpath('//poi')

        for store in data:
            properties = {
                "ref": str(store.xpath('clientkey/text()')[0].extract()),
                "name": store.xpath('name/text()')[0].extract(),
            }

            phone = store.xpath('phone/text()')
            if phone:
                properties['phone'] = phone[0].extract()

            address = self.address(store)
            if address:
                properties.update(address)

            lon_lat = [
                float(store.xpath('longitude/text()')[0].extract()),
                float(store.xpath('latitude/text()')[0].extract()),
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )
