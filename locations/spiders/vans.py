# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.selector import Selector


class VansSpider(scrapy.Spider):
    name = "vans"
    item_attributes = {"brand": "Vans", "brand_wikidata": "Q1135366"}
    allowed_domains = ["locations.vans.com"]
    start_urls = [
        "https://locations.vans.com/01062013/where-to-get-it/ajax?lang=en-EN&xml_request=%3Crequest%3E%3Cappkey%3ECFCAC866-ADF8-11E3-AC4F-1340B945EC6E%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Corder%3E_distance%3C%2Forder%3E%3Csoftmatch%3E1%3C%2Fsoftmatch%3E%3Climit%3E2000%3C%2Flimit%3E%3Catleast%3E1%3C%2Fatleast%3E%3Csearchradius%3E5000%3C%2Fsearchradius%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3EAustin+TX+78702%3C%2Faddressline%3E%3Clongitude%3E%3C%2Flongitude%3E%3Clatitude%3E%3C%2Flatitude%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Cstateonly%3E1%3C%2Fstateonly%3E%3Cnobf%3E1%3C%2Fnobf%3E%3Cwhere%3E%3Ctnvn%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ftnvn%3E%3Cor%3E%3Coff%3E%3Ceq%3ETRUE%3C%2Feq%3E%3C%2Foff%3E%3Cout%3E%3Ceq%3ETRUE%3C%2Feq%3E%3C%2Fout%3E%3Caut%3E%3Ceq%3E%3C%2Feq%3E%3C%2Faut%3E%3Coffer%3E%3Ceq%3E%3C%2Feq%3E%3C%2Foffer%3E%3Cname%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fname%3E%3Ccl%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcl%3E%3Cac%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fac%3E%3Cotw%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fotw%3E%3Ckd%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fkd%3E%3Ccs%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcs%3E%3Cclassicslites%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fclassicslites%3E%3Csf%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fsf%3E%3Cpr%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpr%3E%3Cca%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fca%3E%3Csb%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fsb%3E%3Csn%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fsn%3E%3Cm%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fm%3E%3Cmf%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fmf%3E%3Cga%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fga%3E%3Cgf%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fgf%3E%3Cvl%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fvl%3E%3Cgirlsfootapp%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fgirlsfootapp%3E%3Ccaliuo%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcaliuo%3E%3Ccalinord%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcalinord%3E%3Cebts%3E%3Ceq%3E%3C%2Feq%3E%3C%2Febts%3E%3Clbts%3E%3Ceq%3E%3C%2Feq%3E%3C%2Flbts%3E%3Ccabarbour%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcabarbour%3E%3Cps%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fps%3E%3Cpsnow%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpsnow%3E%3Cpro_shop%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpro_shop%3E%3C%2For%3E%3C%2Fwhere%3E%3C%2Fformdata%3E%3C%2Frequest%3E",
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

            properties = {
                "ref": Selector(text=poi).xpath("//clientkey/text()").get(),
                "name": Selector(text=poi).xpath("//name/text()").get(),
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
