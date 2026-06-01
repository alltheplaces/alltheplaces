import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GBPeterboroughSpider(OwenBaseSpider):
    name = "gb_peterborough"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings                                                                                # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1Bbqkb70BD8D6PjZnTzui4f33ZckZkbUG"
    csv_filename = "PETERBOROUGH_UPRNS_OSOU_202604.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?: ({}))?(?: ({}))$".format(
                "|".join(
                    [
                        # "suburbs"
                        "Ailsworth",
                        "Alwalton",
                        "Bainton",
                        "Barnack",
                        "Bretton",
                        "Castor",
                        "Dogsthorpe",
                        "Eastfield",
                        "Eastgate",
                        "Eye",
                        "Farcet",
                        "Fengate",
                        "Fletton Quays",
                        "Fletton",
                        "Glinton",
                        "Great Haddon",
                        "Gunthorpe",
                        "Hampton Beach",
                        "Hampton Centre",
                        "Hampton Gardens",
                        "Hampton Hargate",
                        "Hampton Heights",
                        "Hampton Vale",
                        "Hampton Water",
                        "Hampton Woods",
                        "Helpston",
                        "Hempsted",
                        "Longthorpe",
                        "Malborne",
                        "Maxey",
                        "Millfield",
                        "Netherton",
                        "New England",
                        "Newborough",
                        "Northborough",
                        "Northminster",
                        "Orton Brimbles",
                        "Orton Goldhay",
                        "Orton Longueville",
                        "Orton Northgate",
                        "Orton Southgate",
                        "Orton Waterville",
                        "Orton Wistow",
                        "Park Farm",
                        "Parnwell",
                        "Paston",
                        "Ravensthorpe",
                        "Stanground South",
                        "Stanground",
                        "Sugar Way",
                        "Thorney",
                        "Thornhaugh",
                        "Ufford",
                        "Walton",
                        "Wansford",
                        "Welland",
                        "Werrington",
                        "West Town",
                        "Westwood",
                        "Wittering",
                        "Woodston",
                        "Wothorpe",
                        "Yaxley",
                    ]
                ),
                "|".join(
                    [
                        # cities
                        "Peterborough",
                        "Stamford",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        addr["ADDR"] = addr["ADDR"].removesuffix(" Cambridgeshire")
        if (
            addr["ADDR"].endswith(" Thorney")
            or addr["ADDR"].endswith(" Helpston")
            or addr["ADDR"].endswith(" Yaxley")
            or addr["ADDR"].endswith(" Newborough")
            or addr["ADDR"].endswith(" Farcet")
            or addr["ADDR"].endswith(" Northborough")
        ):
            addr["ADDR"] += " Peterborough"

        if m := self._re.match(addr["ADDR"].removesuffix(" Cambridgeshire")):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
