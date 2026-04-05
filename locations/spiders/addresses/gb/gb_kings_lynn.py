import csv
import re
from io import BytesIO, TextIOWrapper
from typing import Any
from zipfile import ZipFile

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses


class GbDoncasterSpider(AddressSpider):
    name = "gb_kings_lynn"
    dataset_attributes = Licenses.GB_OGLv3.value | {
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0."  # address strings
        + " Contains OS data © Crown copyright and database right 2025."  # OS Open UPRN, coords
        + " Contains Royal Mail data © Royal Mail copyright and Database right."  # Postcodes
        + " Contains GeoPlace data © Local Government Information House Limited copyright and database right."
        + " Office for National Statistics licensed under the Open Government Licence v.3.0."
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 60 * 5}
    no_refs = True
    start_urls = [
        "https://drive.usercontent.google.com/download?id=1EX1qK63HievHPfIfNEzf9hc2Im8F0gMQ&export=download&confirm=t"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        _re = re.compile(
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

        with ZipFile(BytesIO(response.body)) as zip_file:
            for addr in csv.DictReader(TextIOWrapper(zip_file.open("KLWN_CTBANDS_OSOU_202602.csv"), encoding="utf-8")):
                item = Feature()
                item["ref"] = addr["PROPREF"]
                item["extras"]["ref:GB:uprn"] = addr["UPRN"]
                item["lat"] = addr["LAT"]
                item["lon"] = addr["LNG"]
                item["postcode"] = addr["POSTCODE"]

                if m := _re.match(addr["ADDR"].removesuffix("Norfolk").removesuffix("Cambridgeshire").strip(", ")):
                    item["street_address"], item["extras"]["addr:suburb"], item["city"] = m.groups()

                item["country"] = "GB"

                yield item
