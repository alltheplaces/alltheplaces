import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbNorthNorfolkSpider(OwenBaseSpider):
    name = "gb_north_norfolk"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1IW9mbQIGL0hofzkFWfbBdMZ9kkG_JGCR"
    csv_filename = "NORTHNORFOLK_CTBANDS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?(?:, ({}))$".format(
                "|".join(
                    [
                        "Bacton",
                        "Barningham",
                        "Beeston Regis",
                        "Blakeney",
                        "Briston",
                        "Catfield",
                        "East Runton",
                        "Happisburgh",
                        "Hickling",
                        "Hindringham",
                        "Horning",
                        "Hoveton",
                        "Ludham",
                        "Mundesley",
                        "Northrepps",
                        "Overstrand",
                        "Plumstead",
                        "Potter Heigham",
                        "Scottow",
                        "Sculthorpe",
                        "Southrepps",
                        "Stalham",
                        "Trunch",
                        "Walcott",
                        "West Runton",
                        "Weybourne",
                        "Wicken Green Village",
                    ]
                ),
                "|".join(
                    [
                        "Cromer",
                        "Dereham",
                        "Fakenham",
                        "Great Yarmouth",
                        "Holt",
                        "King's Lynn",
                        "Melton Constable",
                        "North Walsham",
                        "Norwich",
                        "Sheringham",
                        "Walsingham",
                        "Wells-next-the-Sea",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr_str = (
            merge_address_lines([addr["ADDR1"], addr["ADDR2"], addr["ADDR3"], addr["ADDR4"], addr["ADDR5"]])
            .removesuffix("Norfolk")
            .strip(", ")
            .replace(", Kings Lynn", ", King's Lynn")
            .replace(", Wells-next-the-sea", ", Wells-next-the-Sea")
            .replace(", Wells-Next-The-Sea", ", Wells-next-the-Sea")
            .replace(", Wells Next The Sea", ", Wells-next-the-Sea")
            .replace(", Well-next-the-sea", ", Wells-next-the-Sea")
            .replace(", Langham Holt", ", Langham, Holt")
            .replace(", Mundesley Norwich", ", Mundesley, Norwich")
            .replace(", Barningham Norwich", "Barningham, Norwich")
            .replace(", Bacton Norwich", "Bacton, Norwich")
        )
        if addr_str.endswith(", Southrepps") or addr_str.endswith(", Plumstead") or addr_str.endswith(", Stalham"):
            addr_str += ", Norwich"
        elif addr_str.endswith(", Potter Heigham"):
            addr_str += ", Great Yarmouth"
        elif addr_str.endswith(", Hindringham"):
            addr_str += ", Fakenham"

        if m := self._re.match(addr_str):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
            if not item["extras"]["addr:suburb"] and ", " in item["street_address"]:
                self.crawler.stats.inc_value("x/{}".format(item["street_address"].rsplit(", ", 1)[1]))
        else:
            item["addr_full"] = merge_address_lines([addr_str, item.get("postcode")])
