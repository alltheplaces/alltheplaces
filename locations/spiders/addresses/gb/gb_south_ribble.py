from io import BytesIO
from typing import Any

import openpyxl
from scrapy.http import Response

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_28
# https://www.owenboswarva.com/blog/post-addr117.htm


class GbSouthRibbleSpider(UprnEnhancerSpider):
    name = "gb_south_ribble"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # FOI, addr+UPRN
        + " Contains OS data © Crown copyright and database right."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # ONSUD, postcodes
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }
    no_refs = True
    onsud_region = "NW"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_28/response/3515941/attach/6/SRBC269801.xlsx?cookie_passthrough=1"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        rows = openpyxl.load_workbook(BytesIO(response.body), read_only=True).active.iter_rows(values_only=True)
        header = next(rows)

        for row in rows:
            addr = dict(zip(header, row))

            if "DUFF" in addr["addr1"] or "NOT TO BE USED" in addr["addr1"]:
                continue

            item = Feature()
            item["ref"] = str(addr["property_ref1"])

            if addr["uprn"]:
                self.apply_uprn(item, addr["uprn"])

            if not item.get("city") and item.get("postcode"):
                item["city"] = self.postal_towns.get(item["postcode"].split(" ", 1)[0])

            item["addr_full"] = merge_address_lines(
                [
                    addr["addr1"],
                    addr["addr2"],
                    addr["addr3"],
                    item.get("postcode"),
                ]
            ).removesuffix(", LANCASHIRE")

            yield item
