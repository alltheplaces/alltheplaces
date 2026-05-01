import re
from typing import Any, Self

from scrapy.crawler import Crawler

from locations.items import Feature
from locations.licenses import Licenses
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.owen_base_spider import OwenBaseSpider


class GbKingsLynnSpider(OwenBaseSpider):
    name = "gb_kings_lynn"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }

    drive_id = "1EX1qK63HievHPfIfNEzf9hc2Im8F0gMQ"
    csv_filename = "KLWN_CTBANDS_OSOU_202602.csv"

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._re = re.compile(
            r"^(.+?)(?:, ({}))?(?:, ({}))?$".format(
                "|".join(
                    [
                        # "suburbs"
                        "Heacham",
                        "Dersingham",
                        "South Wootton",
                        "Terrington St Clement",
                        "Snettisham",
                        "Emneth",
                        "Feltwell",
                        "West Winch",
                        "Watlington",
                        "Upwell",
                        "Outwell",
                        "North Wootton",
                        "Clenchwarton",
                        "West Lynn",
                        "Gayton",
                        "Gaywood",
                        "Docking",
                        "Walsoken",
                        "Burnham Market",
                        "Upper Marham",
                        "Southery",
                        "Marshland St James",
                        "Methwold",
                        "Tilney St Lawrence",
                        "West Walton",
                        "Stoke Ferry",
                        "Pott Row",
                        "Middleton",
                        "Castle Acre",
                        "Great Massingham",
                        "Hilgay",
                        "Northwold",
                        "Walpole St Andrew",
                        "Denver",
                        "Wiggenhall St Germans",
                        "Terrington St John",
                        "Grimston",
                        "Brancaster",
                        "Marham",
                        "Ingoldisthorpe",
                        "Walpole St Peter",
                        "Thornham",
                        "Walpole Highway",
                        "Old Hunstanton",
                        "Stow Bridge",
                        "Wimbotsham",
                        "East Winch",
                        "South Creake",
                        "Wereham",
                        "Brancaster Staithe",
                        "Sedgeford",
                        "Pentney",
                        "Tilney All Saints",
                        "Wiggenhall St Mary Magdalen",
                        "Hockwold cum Wilton",
                        "Syderstone",
                        "Shouldham",
                        "East Rudham",
                        "Walton Highway",
                        "Fincham",
                        "Runcton Holme",
                        "Welney",
                        "North Creake",
                        "Holme Next The Sea",
                        "Barroway Drove",
                        "Nordelph",
                        "Ringstead",
                    ]
                ),
                "|".join(
                    [
                        # cities
                        "King'?s Lynn",
                        "Downham Market",
                        "Wisbech",
                        "Hunstanton",
                        "Thetford",
                        "Fakenham",
                        "Sandringham",
                        "Ely",
                        "Snettisham",
                    ]
                ),
            )
        )
        return spider

    def parse_row(self, item: Feature, addr: dict):
        if m := self._re.match(addr["ADDR"].removesuffix("Norfolk").removesuffix("Cambridgeshire").strip(", ")):
            item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()
        else:
            item["addr_full"] = merge_address_lines([addr["ADDR"], item.get("postcode")])
