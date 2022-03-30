import scrapy
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAYS_NAME = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}

HEADERS = {"Accept": "application/json"}


class KateSpade(scrapy.Spider):
    name = "katespade"
    allowed_domains = ["katespade.com", "katespade.brickworksoftware.com"]

    def start_requests(self):
        yield scrapy.Request(
            "https://katespade.brickworksoftware.com/locations_search?esSearch=%7B%22page%22:1,%22storesPerPage%22:50,%22domain%22:%22katespade.brickworksoftware.com%22,%22locale%22:%22en_US%22,%22must%22:[%7B%22type%22:%22range%22,%22field%22:%22published_at%22,%22value%22:%7B%22lte%22:1576183550804%7D%7D],%22filters%22:[],%22aroundLatLng%22:%7B%22lat%22:%2231%22,%22lon%22:%22-100%22%7D%7D",
            headers=HEADERS,
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if hour["type"] == "regular":
                try:
                    day = DAYS_NAME[hour["displayDay"]]
                    open_time = hour["displayStartTime"].strip()
                    close_time = hour["displayEndTime"].strip()
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%I:%M%p",
                    )
                except:
                    pass

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        stores = stores["hits"]

        if stores:

            for store in stores:

                properties = {
                    "ref": store["id"],
                    "name": store["attributes"]["name"],
                    "addr_full": " ".join(
                        [
                            store["attributes"]["address1"],
                            store.get("address2", ""),
                            store.get("address3", ""),
                        ]
                    ).strip(),
                    "city": store["attributes"]["city"],
                    "state": store["attributes"]["state"],
                    "postcode": store["attributes"]["postalCode"],
                    "phone": store["attributes"]["phoneNumber"],
                    "website": store["domain"],
                    "lat": store["attributes"]["latitude"],
                    "lon": store["attributes"]["longitude"],
                }

                opening_hours = self.parse_hours(store["relationships"]["hours"])
                if opening_hours:
                    properties["opening_hours"] = opening_hours

                yield GeojsonPointItem(**properties)

            page = int(re.search(r"page%22:(\d+)", response.url).groups()[0])
            url = response.urljoin(
                response.url.replace(
                    "page%22:{}".format(page), "page%22:{}".format(page + 1)
                )
            )

            yield scrapy.Request(url, headers=HEADERS)
