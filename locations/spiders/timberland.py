# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.selector import Selector


class TimberlandSpider(scrapy.Spider):
    name = "timberland"
    item_attributes = {"brand": "Timberland"}
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = [
        "https://hosted.where2getit.com/timberland/local/ajax?lang=en-EN&xml_request=%3Crequest%3E%3Cappkey%3E3BD8F794-CA9E-11E5-A9D5-072FD1784D66%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Corder%3Eretail_store%2Cfactory_outlet%2Crank+ASC%2C_distance%3C%2Forder%3E%3Climit%3E2000%3C%2Flimit%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3EAustin+TX+78702%3C%2Faddressline%3E%3Clongitude%3E%3C%2Flongitude%3E%3Clatitude%3E%3C%2Flatitude%3E%3Ccountry%3E%3C%2Fcountry%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Cradiusuom%3E%3C%2Fradiusuom%3E%3Csearchradius%3E5000%7C75%3C%2Fsearchradius%3E%3Cwhere%3E%3Cor%3E%3Cretail_store%3E%3Ceq%3E1%3C%2Feq%3E%3C%2Fretail_store%3E%3Cfactory_outlet%3E%3Ceq%3E1%3C%2Feq%3E%3C%2Ffactory_outlet%3E%3Cauthorized_reseller%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fauthorized_reseller%3E%3Cicon%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ficon%3E%3Cpro_workwear%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpro_workwear%3E%3Cpro_footwear%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpro_footwear%3E%3C%2For%3E%3C%2Fwhere%3E%3C%2Fformdata%3E%3C%2Frequest%3E"
    ]

    def parse(self, response):
        xxs = Selector(response)

        pois = xxs.xpath("//poi").extract()

        for poi in pois:
            state = Selector(text=poi).xpath("//state/text()").get()
            if state == None:
                state = Selector(text=poi).xpath("//province/text()").get()

            addr = Selector(text=poi).xpath("//address1/text()").get()
            if addr == None:
                addr = Selector(text=poi).xpath("//address2/text()").get()
                if addr == None:
                    addr = Selector(text=poi).xpath("//dsply_adr/text()").get()

            name = Selector(text=poi).xpath("//name/text()").get()
            name = name.replace("<br>", "")
            name = name.replace("&reg", " ")
            name = name.replace(";", "")
            name = name.replace("  ", " ")

            properties = {
                "ref": Selector(text=poi).xpath("//clientkey/text()").get(),
                "name": name,
                "addr_full": addr,
                "city": Selector(text=poi).xpath("//city/text()").get(),
                "state": state,
                "postcode": Selector(text=poi).xpath("//postalcode/text()").get(),
                "country": Selector(text=poi).xpath("//country/text()").get(),
                "lat": Selector(text=poi).xpath("//latitude/text()").get(),
                "lon": Selector(text=poi).xpath("//longitude/text()").get(),
                "phone": Selector(text=poi).xpath("//phone/text()").get(),
            }

            yield GeojsonPointItem(**properties)
