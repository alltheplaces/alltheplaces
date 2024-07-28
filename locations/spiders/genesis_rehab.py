import json

import scrapy

from locations.items import Feature

st = [
    "1:AL",
    "3:AZ",
    "5:CA",
    "6:CO",
    "7:CT",
    "8:DE",
    "13:ID",
    "18:KY",
    "20:ME",
    "21:MD",
    "22:MA",
    "30:NH",
    "31:NJ",
    "32:NM",
    "34:NC",
    "39:PA",
    "40:RI",
    "43:TN",
    "46:VT",
    "47:VA",
    "48:WA",
    "49:WV",
]


class GenesisRehabSpider(scrapy.Spider):
    name = "genesis_rehab"
    item_attributes = {"brand": "Genesis Rehab Services", "brand_wikidata": "Q5532813"}
    allowed_domains = ["genesishcc.com"]
    start_urls = ("https://www.genesishcc.com/page-data/findlocations/page-data.json",)

    def parse(self, response):
        data = json.loads(json.dumps(response.xpath("/html/body").extract()))
        data2 = data[0].split('}}}}]}}},{"node')
        for j in data2[1:]:
            datalist = j.split(",")

            for i in datalist:
                if i.startswith('"field_latitude'):
                    lat = float(i.split(":")[1].strip('"'))
                elif i.startswith('"field_longitude"'):
                    lon = float(i.split(":")[1].strip('"'))
                elif i.startswith('"field_address'):
                    address = i.split(":")[1].strip('"')
                elif i.startswith('"field_city'):
                    city = i.split(":")[1].strip('"')
                elif i.startswith('"field_state'):
                    statecode = i.split(":")[1].strip('"')
                    for sts in st:
                        if sts.split(":")[0] == statecode:
                            state = sts.split(":")[1]
                        else:
                            pass
                elif i.startswith('"field_zip'):
                    zip = i.split(":")[1].strip('"')
                else:
                    pass

            properties = {
                "ref": address + state + city,
                "name": "Genesis Healthcare",
                "street_address": address,
                "city": city,
                "state": state,
                "postcode": zip,
                "country": "US",
                "lat": lat,
                "lon": lon,
            }

            yield Feature(**properties)
