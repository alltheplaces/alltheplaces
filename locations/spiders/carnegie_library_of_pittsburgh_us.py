from typing import Iterable

from scrapy.http import Request, TextResponse

from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider


class CarnegieLibraryOfPittsburghUSSpider(LibCalSpider):
    name = "carnegie_library_of_pittsburgh_us"
    item_attributes = {"operator": "Carnegie Library of Pittsburgh", "operator_wikidata": "Q5043945"}
    libcal_host = "carnegielibrary.libcal.com"
    libcal_iid = 4739
    country = "US"

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        name = (item.pop("name") or "").strip()
        if not name.startswith("CLP"):
            # "ACLL Allegheny County Law Library" is run by the Allegheny
            # County courts and only shares this LibCal tenant.
            return
        # "CLP - Beechview", but "CLP-LAMP/Library of Accessible Media for
        # Pennsylvanians" for the accessible media library.
        item["branch"] = name.removeprefix("CLP").lstrip(" -").split("/", 1)[-1]
        item["name"] = "Carnegie Library of Pittsburgh - {}".format(item["branch"])
        yield item
