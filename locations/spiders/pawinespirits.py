import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class PAWineSpiritsSpider(scrapy.Spider):
    name = "pawinespirits"
    item_attributes = {
        "name": "Fine Wine & Good Spirits",
        "brand": "Fine Wine & Good Spirits",
        "brand_wikidata": "Q64514776",
    }
    allowed_domains = ["www.finewineandgoodspirits.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://www.finewineandgoodspirits.com/webapp/wcs/stores/servlet/FindStoreView?storeId=10051&langId=-1&catalogId=10051&pageNum=1&listSize=1000&category=&city=&zip_code=&county=All+Stores&storeNO="
        yield scrapy.http.Request(url, self.parse)

    def parse(self, response):
        for row in response.css(".tabContentRow"):
            column_address = row.css(".columnAddress")
            address_phone_fax = [s.strip() for s in column_address.xpath('*[@class="normalText"]//text()').extract()]
            if "Fax:" in address_phone_fax:
                i = address_phone_fax.index("Fax:")
                fax = address_phone_fax[i + 1]
                address_phone_fax[i:] = []
            else:
                fax = None
            i = address_phone_fax.index("Phone:")
            phone = address_phone_fax[i + 1]
            address_phone_fax[i:] = []
            address = "\n".join(address_phone_fax).strip().replace("\xa0", " ")

            ref = column_address.xpath('*[@class="boldMaroonText"]/text()').get().strip()

            type_text = [s.strip() for s in row.xpath('*[@class="columnTypeOfStore"]//text()').extract()]
            type_of_store = [s for s in type_text if s]

            hours_txt = row.xpath('*[@class="columnHoursOfOprn"]/div/*/text()').extract()
            opening_hours = [
                f"{hours_txt[i]} {hours_txt[i + 1]}"
                for i in range(0, len(hours_txt) // 2, 2)
                if hours_txt[i + 1] != "Closed"
            ]
            oh = OpeningHours()
            oh.from_linked_data({"openingHours": opening_hours}, "%I:%M %p")

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
                "opening_hours": oh.as_opening_hours(),
            }
            yield Feature(**properties)
