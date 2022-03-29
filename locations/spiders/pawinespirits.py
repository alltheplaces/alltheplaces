import re
import urllib

import scrapy
from locations.items import GeojsonPointItem


class PAWineSpirits(scrapy.Spider):
    name = "pawinespirits"
    item_attributes = {
        "name": "Fine Wine & Good Spirits",
        "brand": "Fine Wine & Good Spirits",
        "brand_wikidata": "Q64514776",
    }
    allowed_domains = ["www.finewineandgoodspirits.com"]

    def start_requests(self):
        url = "https://www.finewineandgoodspirits.com/webapp/wcs/stores/servlet/FindStoreView?storeId=10051&langId=-1&catalogId=10051&pageNum=1&listSize=1000&category=&city=&zip_code=&county=All+Stores&storeNO="
        yield scrapy.http.Request(url, self.parse)

    def parse(self, response):
        for row in response.css(".tabContentRow"):
            columnAddress = row.css(".columnAddress")
            addressPhoneFax = [
                s.strip()
                for s in columnAddress.xpath('*[@class="normalText"]//text()').extract()
            ]
            if "Fax:" in addressPhoneFax:
                i = addressPhoneFax.index("Fax:")
                fax = addressPhoneFax[i + 1]
                addressPhoneFax[i:] = []
            else:
                fax = None
            i = addressPhoneFax.index("Phone:")
            phone = addressPhoneFax[i + 1]
            addressPhoneFax[i:] = []
            address = "\n".join(addressPhoneFax).strip().replace("\xa0", " ")

            ref = columnAddress.xpath('*[@class="boldMaroonText"]/text()').get().strip()

            type_text = [
                s.strip()
                for s in row.xpath('*[@class="columnTypeOfStore"]//text()').extract()
            ]
            type_of_store = [s for s in type_text if s]

            hours_txt = row.xpath(
                '*[@class="columnHoursOfOprn"]/div/*/text()'
            ).extract()
            hour_pairs = list(zip(*[iter(hours_txt)] * 2))
            hours = ", ".join(" ".join(x) for x in hour_pairs)

            [lat, lon] = row.xpath("*/form/input").re('name=".*itude" value="(.*)"')
            if float(lat) == 0 and float(lon) == 0:
                lat, lon = None, None

            properties = {
                "lat": lat,
                "lon": lon,
                "addr_full": address,
                "phone": phone,
                "extras": {
                    "fax": fax,
                    "shop": "alcohol",
                    "type_of_store": type_of_store,
                },
                "ref": ref,
                "opening_hours": hours,
            }
            yield GeojsonPointItem(**properties)
