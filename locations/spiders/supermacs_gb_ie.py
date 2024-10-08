from typing import Any, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class SupermacsGBIESpider(Spider):
    name = "supermacs_gb_ie"
    item_attributes = {
        "brand_wikidata": "Q7643750",
        "brand": "Supermac's",
    }
    allowed_domains = [
        "supermacs.ie",
    ]

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            "https://supermacs.ie/wp-admin/admin-ajax.php",
            formdata={"action": "get_markers"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["markers"]:
            item = DictParser().parse(location)
            item["website"] = location["store_link"]
            if location["store_front_image"]:
                item["image"] = location["store_front_image"]["url"]
            item["phone"] = location["store_telephone"]
            item["addr_full"] = item["addr_full"].replace("<br />", "")
            item["ref"] = item["website"]

            # TODO: Parse the HTML table of hours
            # item["opening_hours"] = OpeningHours()
            # item["opening_hours"].add_ranges_from_string(location["store_opening_hours"])
            # print(location["store_opening_hours"].replace(' style="text-align: center;"', "").replace('<td class="center">&#8211;</td>', ''))
            # <table id="store-schedule">
            # <tbody>
            # <tr>
            # <th>Monday</th>
            # <th>Tuesday</th>
            # <th>Wednesday</th>
            # <th>Thursday</th>
            # <th>Friday</th>
            # <th>Saturday</th>
            # <th>Sunday</th>
            # </tr>
            # <tr>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # </tr>
            # <tr>
            # </tr>
            # <tr>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # </tr>
            # </tbody>
            # </table>
            # <p>&nbsp;</p>
            # <p><b>Christmas and New Years 2023</b></p>
            # <table style="width: 100%;">
            # <tbody>
            # <tr>
            # <th>24th Dec</th>
            # <th>25th Dec</th>
            # <th>26th Dec</th>
            # <th>27th Dec</th>
            # <th>28th Dec</th>
            # <th>29th Dec</th>
            # <th>30th Dec</th>
            # <th>31st Dec/1st Jan</th>
            # </tr>
            # <tr>
            # <td>9:00</td>
            # <td>Closed</td>
            # <td>12:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00</td>
            # <td>9:00 / 22:00</td>
            # </tr>
            # <tr></tr>
            # <tr>
            # <td>20:00</td>
            # <td>Closed</td>
            # <td>22:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>23:00</td>
            # <td>12:00 / 23:00</td>
            # </tr>
            # </tbody>
            # </table>
            # <p>&nbsp;</p>

            yield item
