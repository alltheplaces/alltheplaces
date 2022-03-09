# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class QuiktripSpider(scrapy.Spider):
    name = "quiktrip"
    item_attributes = {"brand": "QuikTrip", "brand_wikidata": "Q7271953"}
    allowed_domains = ["quiktrip.com", "where2getit.com"]
    start_urls = (
        "https://hosted.where2getit.com/quiktrip/ajax?&xml_request=%3Crequest%3E%3Cappkey%3E82C11D38-0EC6-11E0-8AD9-4C59241F5146%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Climit%3E1000%3C%2Flimit%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3Ekansas%3C%2Faddressline%3E%3Clongitude%3E%3C%2Flongitude%3E%3Clatitude%3E%3C%2Flatitude%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Csearchradius%3E1400%3C%2Fsearchradius%3E%3Cwhere%3E%3Ctravelcenter%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ftravelcenter%3E%3Ctruckdiesel%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ftruckdiesel%3E%3Ce15%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fe15%3E%3Cautodiesel%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fautodiesel%3E%3Cspecialtydrinks%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fspecialtydrinks%3E%3Cgen3%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fgen3%3E%3Chotandfreshpretzels%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fhotandfreshpretzels%3E%3Chotsandwiches%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fhotsandwiches%3E%3Cxlpizza%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fxlpizza%3E%3Cpersonalpizzas%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fpersonalpizzas%3E%3Cnoethanol%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fnoethanol%3E%3Ccertifiedscales%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fcertifiedscales%3E%3Cdef%3E%3Ceq%3E%3C%2Feq%3E%3C%2Fdef%3E%3Cfrozentreats%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ffrozentreats%3E%3Cfreshbrewedtea%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ffreshbrewedtea%3E%3Cfrozendrinks%3E%3Ceq%3E%3C%2Feq%3E%3C%2Ffrozendrinks%3E%3C%2Fwhere%3E%3C%2Fformdata%3E%3C%2Frequest%3E",
    )

    def parse(self, response):
        shops = response.xpath("//collection/poi")

        def has_feature(shop, feature):
            return shop.xpath(f".//{feature}/text()").extract_first() == "1"

        for shop in shops:
            yield GeojsonPointItem(
                ref=shop.xpath(".//clientkey/text()").extract_first(),
                phone=shop.xpath(".//phone/text()").extract_first(),
                addr_full=shop.xpath(".//address1/text()").extract_first(),
                postcode=shop.xpath(".//postalcode/text()").extract_first(),
                city=shop.xpath(".//city/text()").extract_first(),
                state=shop.xpath(".//state/text()").extract_first(),
                country=shop.xpath(".//country/text()").extract_first(),
                lat=float(shop.xpath(".//latitude/text()").extract_first()),
                lon=float(shop.xpath(".//longitude/text()").extract_first()),
                extras={
                    "amenity:fuel": True,
                    "atm": has_feature(shop, "atm"),
                    "fuel:diesel": has_feature(shop, "autodiesel")
                    or has_feature(shop, "truckdiesel"),
                    "fuel:e15": has_feature(shop, "e15"),
                    "fuel:HGV_diesel": has_feature(shop, "truckdiesel"),
                    "hgv": has_feature(shop, "truckdiesel")
                    or has_feature(shop, "certifiedscales"),
                },
            )
