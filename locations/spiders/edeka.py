# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class EdekaSpider(scrapy.Spider):
    """Scrapes Edeka, the German market chain, locations."""

    name = "edeka"
    item_attributes = {"brand": "Edeka", "brand_wikidata": "Q701755"}
    allowed_domains = ["www.edeka.de"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        """Initial Request. The initial request searches for all Edeka locations within the rectangle 47.0 South, 55.5 North, 5.62 East, 15 west"""
        url = "https://www.edeka.de/search.xml"
        yield scrapy.Request(
            url,
            method="POST",
            headers={
                "referer": "https://edeka.de/marktsuche.jsp",
                "content-type": "application/x-www-form-urlencoded",
            },
            body="indent=off&hl=false&rows=10000&q=(indexName:b2cMarktDBIndex++AND+kanalKuerzel_tlcm:edeka+AND+((freigabeVonDatum_longField_l:[0+TO+1513897199999]+AND+freigabeBisDatum_longField_l:[1513810800000+TO+*])+AND+NOT+(datumAppHiddenVon_longField_l:[0+TO+1513897199999]+AND+datumAppHiddenBis_longField_l:[1513810800000+TO+*]))+AND+geoLat_doubleField_d:[47.0+TO+55.0]+AND+geoLng_doubleField_d:[5.62+TO+15])&fl=handzettelSonderlUrl_tlcm,handzettelSonderName_tlcm,handzettelUrl_tlc,marktID_tlc,plz_tlc,ort_tlc,strasse_tlc,name_tlc,geoLat_doubleField_d,geoLng_doubleField_d,telefon_tlc,fax_tlc,services_tlc,oeffnungszeiten_tlc,knzUseUrlHomepage_tlc,urlHomepage_tlc,urlExtern_tlc,marktTypName_tlc,mapsBildURL_tlc,vertriebsschieneName_tlc,vertriebsschienenTypeKuerzel_tlc,vertriebsschieneKey_tlc,freigabeVonDatum_longField_l,freigabeBisDatum_longField_l,datumAppHiddenVon_longField_l,datumAppHiddenBis_longField_l,oeffnungszeitenZusatz_tlc,knzTz_tlc,kaufmannIName_tlc,kaufmannIStrasse_tlc,kaufmannIPlz_tlc,kaufmannIOrt_tlc,sonderoeffnungszeitJahr_tlcm,sonderoeffnungszeitMonat_tlcm,sonderoeffnungszeitTag_tlcm,sonderoeffnungszeitUhrzeitBis_tlcm,sonderoeffnungszeitUhrzeitVon_tlcm,regionName_tlc",
        )  # The request body contains the coordinates past the edges of Germany. Gets all the stores in Germany

    def parse(self, response):
        store_data = response.json()["response"]["docs"]

        for store in store_data:
            properties = {
                "ref": store["marktID_tlc"],
                "name": store["name_tlc"],
                "addr_full": store["strasse_tlc"],
                "city": store["ort_tlc"],
                "state": store["regionName_tlc"],
                "postcode": store["plz_tlc"],
                "country": "DE",
                "lat": store["geoLat_doubleField_d"],
                "lon": store["geoLng_doubleField_d"],
                "phone": store["telefon_tlc"],
            }

            yield GeojsonPointItem(**properties)
