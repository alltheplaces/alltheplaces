import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbBasildonSpider(OwenBaseSpider):
    name = "gb_basildon"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."
        + " Contains OS data © Crown copyright and database right 2026."
        + " Contains Royal Mail data © Royal Mail copyright and Database right."
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1ynWsQ1V04MRn_VqtVJUuFWNC-NcEnvFg"
    csv_filename = "BASILDON_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Barstable",
                        "Crays Hill",
                        "Fryerns",
                        "Kingswood",
                        "Laindon",
                        "Langdon Hills",
                        "Noak Bridge",
                        "North Benfleet",
                        "Pitsea",
                        "Shotgate",
                        "Vange",
                    ]
                ),
                "|".join(["Basildon", "Benfleet", "Billericay", "Brentwood", "Stanford-le-Hope", "Wickford"]),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], addr["ADDR5"]])
            .removesuffix(" Essex")
            .strip(", ")
            .replace(", Basildon, Laindon", ", Laindon, Basildon")
            .replace(", Basildon, Pitsea", ", Pitsea, Basildon")
            .replace(", Basildon, Langdon Hills", ", Langdon Hills, Basildon")
            .replace(", Basildon, Vange", ", Vange, Basildon")
            .replace(", Basildon, Bowers Gifford", ", Bowers Gifford, Basildon")
            .replace(", Basildon, North Benfleet", ", North Benfleet, Basildon")
            .replace(", Billericay, Burstead", ", Burstead, Billericay")
            .replace(", Wickford, North Benfleet", ", North Benfleet, Wickford")
            .replace(", Basildon Basildon", ", Basildon")
            .replace(", Basildon, Noakbridge Laindon", ", Noakbridge Laindon, Basildon")
            .replace(", Stanford-le-hope", ", Stanford-le-Hope")
            .replace(", Stanford-Le-Hope", ", Stanford-le-Hope")
        )

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
