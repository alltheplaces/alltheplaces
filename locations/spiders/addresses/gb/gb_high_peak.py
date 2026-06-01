import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbHighPeakSpider(OwenBaseSpider):
    name = "gb_high_peak"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1yaYkG8OGMsed8EeSCIRVKViw15CPnRYc"
    csv_filename = "HIGHPEAK_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?, ({})$".format(
                "|".join(
                    [
                        "Bamford",
                        "Birch Vale",
                        "Buxworth",
                        "Castleton",
                        "Chapel-En-Le-Frith",
                        "Charlesworth",
                        "Chinley",
                        "Chisworth",
                        "Combs",
                        "Dove Holes",
                        "Edale",
                        "Fairfield",
                        "Furness Vale",
                        "Gamesley",
                        "Hadfield",
                        "Harpur Hill",
                        "Hayfield",
                        "Hollingworth",
                        "Hope",
                        "New Mills",
                        "Padfield",
                        "Peak Dale",
                        "Peak Forest",
                        "Simmondley",
                        "Tintwistle",
                        "Whaley Bridge",
                    ]
                ),
                "|".join(
                    [
                        "Buxton",
                        "Glossop",
                        "High Peak",
                        "Hope Valley",
                        "Hyde",
                        "Stockport",
                        "Sheffield",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"]])
            .removesuffix(", Derbyshire")
            .removesuffix(", Derbyshiire")
            .removesuffix(", Derbyshhire")
            .removesuffix(", Cheshire")
            .removesuffix(", Chehsire")
            .removesuffix(", Derbys")
            .replace(", Glosop", ", Glossop")
            .replace(", High Peak High Peak", ", High Peak")
            .replace(", Buxton Derbyshire", ", Buxton")
            .replace(", Glossop Derbyshire", ", Glossop")
            .replace(", Glossop, Derbys", ", Glossop")
            .replace(", Hadfield Glossop", ", Hadfield, Glossop")
            .replace(", High Peak, High Peal", ", High Peak")
            .replace(", Hollingworth Hyde", ", Hollingworth, Hyde")
            .replace(", Glososp", ", Glossop")
            .replace(", Chapel-en-le-Frith", ", Chapel-En-Le-Frith")
            .replace(", Chapel En Le Frith", ", Chapel-En-Le-Frith")
            .replace(", Chapel En Frith", ", Chapel-En-Le-Frith")
            .replace(", Simmondley Glossop", ", Simmondley, Glossop")
            .replace(", Harpur Hill Buxton", ", Harpur Hill, Buxton")
        )

        if addr_str.endswith(", Hollingworth"):
            addr_str += ", Hyde"
        elif (
            addr_str.endswith(", Chapel-En-Le-Frith")
            or addr_str.endswith(", Hayfield")
            or addr_str.endswith(", New Mills")
            or addr_str.endswith(", Whaley Bridge")
            or addr_str.endswith(", Furness Vale")
            or addr_str.endswith(", Buxworth")
        ):
            addr_str += ", High Peak"
        elif addr_str.endswith(", Bamford") or addr_str.endswith(", Castleton"):
            addr_str += ", Hope Valley"
        elif addr_str.endswith(", Hadfield"):
            addr_str += ", Glossop"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
