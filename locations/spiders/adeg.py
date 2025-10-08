import scrapy

from locations.hours import OpeningHours
from locations.items import Feature

wochentag = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}


class AdegSpider(scrapy.Spider):
    name = "adeg"
    item_attributes = {"brand": "ADEG", "brand_wikidata": "Q290211"}
    allowed_domains = ["adeg.at"]

    def start_requests(self):
        yield self.get_page(1)

    def get_page(self, n):
        return scrapy.Request(
            f"https://www.adeg.at/services/maerkte-oeffnungszeiten?tx_solr[page]={n}&type=7382&distance=1000",
            meta={"page": n},
        )

    def parse(self, response):
        stores = response.json()["merchantData"]
        if stores == []:
            return
        yield self.get_page(1 + response.meta["page"])

        for store in stores:
            lat, lon = store["coordinates"].split(",")

            oh = OpeningHours()
            for row in scrapy.Selector(text=store["openingHours"]).xpath(".//dt"):
                day = wochentag[row.xpath("normalize-space()").get().removesuffix(":")]
                for interval in row.xpath("./following-sibling::dd[position()=1]/span/text()").extract():
                    open_time, close_time = interval.strip(",").split(" \u2013 ")
                    if (open_time, close_time) == ("", ""):
                        continue
                    oh.add_range(day, open_time, close_time)

            properties = {
                "ref": store["uid"],
                "lat": lat,
                "lon": lon,
                "name": store["title"],
                "street_address": store["street"],
                "city": store["municipality"],
                "postcode": store["zip"],
                "country": "AT",
                "phone": store["telephoneUrl"].removeprefix("tel:"),
                "website": response.urljoin(store["url"]),
                "opening_hours": oh.as_opening_hours(),
            }
            yield Feature(**properties)
