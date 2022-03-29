import scrapy
from six.moves.urllib.parse import urlencode
from locations.items import GeojsonPointItem

LAT_LONS = [
    # Northeast locations
    ("37.7666545", "-74.8088835"),
    ("37.21232025", "-76.47188625"),
    ("37.21232025", "-77.58055475"),
    ("38.32098875", "-76.47188625"),
    ("38.32098875", "-77.58055475"),
    ("39.152490125", "-74.531716375"),
    ("39.706824375", "-73.977382125"),
    ("39.706824375", "-74.531716375"),
    ("39.152490125", "-75.0860506250"),
    ("39.152490125", "-75.640384875"),
    ("39.5682408125", "-74.9474670625"),
    ("39.5682408125", "-75.2246341875"),
    ("39.8454079375", "-74.9474670625"),
    ("39.8454079375", "-75.2246341875"),
    ("39.706824375", "-75.640384875"),
    ("40.53832575", "-74.25454925"),
    ("40.1225750625", "-74.9474670625"),
    ("40.1225750625", "-75.2246341875"),
    ("40.3997421875", "-74.9474670625"),
    ("40.3997421875", "-75.2246341875"),
    ("40.261158625", "-75.640384875"),
    ("40.815492875", "-75.0860506250"),
    ("40.815492875", "-75.640384875"),
    ("39.9839915", "-77.0262205"),
    ("39.9888", "-75.4026"),
    ("39.984", "-75.101"),
    ("40.128", "-74.707"),
    # Florida Locations
    ("25.9939", "-80.2966"),  # Most southern store location
    ("27.4473", "-82.5758"),  # Sarasota area locations
    ("28.0692", "-82.4306"),  # Tampa North area locations
    ("28.2288", "-81.6487"),  # Orlando area locations
    ("30.2704", "-81.7560"),  # Jacksonville area locations
]


class WawaSpider(scrapy.Spider):
    name = "wawa"
    item_attributes = {"brand": "Wawa"}
    start_urls = ("https://www.wawa.com/Handlers/LocationByLatLong.ashx?",)
    download_delay = 1.5
    allowed_domains = "www.wawa.com"

    def start_requests(self):
        url = "https://www.wawa.com/Handlers/LocationByLatLong.ashx?"
        for lat, lon in LAT_LONS:
            wawa_params = {"limit": 50, "lat": lat, "long": lon}

            yield scrapy.Request(
                url + urlencode(wawa_params),
                headers={
                    "Accept": "application/json",
                },
                callback=self.parse,
            )

    def get_addr(self, addr):
        return (v for k, v in addr.items() if k in ["address", "city", "state", "zip"])

    def get_lat_lng(self, physical_addr):
        return physical_addr["loc"]

    def get_opening_hours(self, store):
        open_time = store["storeOpen"][:5]
        close_time = store["storeClose"][:5]

        times = "{}-{}".format(open_time, close_time)

        if times == "00:00-00:00":
            return "24/7"
        else:
            return times

    def parse(self, response):
        wawa_stores = response.json()

        for loc in wawa_stores["locations"]:

            addr, city, state, zipc = self.get_addr(loc["addresses"][0])
            lat, lng = self.get_lat_lng(loc["addresses"][1])
            opening_hours = self.get_opening_hours(loc) or None

            properties = {
                "addr_full": addr,
                "name": loc["storeName"],
                "phone": loc["telephone"],
                "city": city,
                "state": state,
                "postcode": zipc,
                "ref": loc["locationID"],
                "website": "https://www.wawa.com/stores/{}/{}".format(
                    loc["locationID"],
                    loc["addressUrl"],
                ),
                "lat": float(lat),
                "lon": float(lng),
                "opening_hours": opening_hours,
            }

            yield GeojsonPointItem(**properties)
