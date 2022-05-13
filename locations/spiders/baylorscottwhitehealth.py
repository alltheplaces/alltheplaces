import scrapy
from locations.items import GeojsonPointItem


class BaylorScottWhiteSpider(scrapy.Spider):
    name = "baylorscottwhite"
    item_attributes = {
        "brand": "Baylor Scott & White Health",
        "brand_wikidata": "Q41568258",
    }
    allowed_domains = ["www.bswhealth.com", "phyndapi.bswapi.com"]
    start_urls = ("https://www.bswhealth.com/",)

    def start_requests(self):
        url = "https://phyndapi.bswapi.com/V2/Places/GetLocations?&location=30.259317199999998,-97.7393817&distance=100000&LineOfBusiness=BSWH&pageNumber=1&sortSeed=1049&perPage=1000&SortBy=Distance&DocSortBy=NextAvailableAppointment&overrideRules=false"

        headers = {
            "Referer": "https://www.bswhealth.com/",
            "Cookie": "ARRAffinity=abb1bf08643cf24445e2af4eb0b40e562ee3a33b388db503d33b42e5adafc29f;Path=/;HttpOnly;Secure;Domain=phyndapi.bswapi.com",
            "Authorization": "phyndapi.bswapi.com",
            "x-bsw-clientid": "BSWHealth.com",
        }

        yield scrapy.http.FormRequest(
            url,
            self.parse,
            method="GET",
            headers=headers,
        )

    def parse(self, response):
        ldata = response.json()

        ldata = ldata["locationResults"]

        for row in ldata:

            properties = {
                "ref": row["locationID"],
                "name": row["locationName"],
                "addr_full": " ".join(
                    [row["locationStreet1"], row.get("locationStreet2", "") or ""]
                ).strip(),
                "city": row["locationCity"],
                "postcode": row["locationZip"],
                "state": row["locationState"],
                "lat": row["coordinates"]["lat"],
                "lon": row["coordinates"]["lon"],
                "phone": row["locationPhone"],
                "website": row["locationUrl"],
            }

            yield GeojsonPointItem(**properties)
