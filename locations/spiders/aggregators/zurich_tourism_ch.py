import re
from typing import Any, AsyncIterator, Iterable, Tuple

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.licenses import Licenses

# Mix of schema.org and made-up non-standard categories.
ZURICH_TOURISM_CATEGORIES = {
    "ArtGallery": Categories.TOURISM_GALLERY,
    "ArtObject": Categories.TOURISM_ARTWORK,
    "BarOrPub": Categories.BAR,
    "BedAndBreakfast": Categories.TOURISM_BED_AND_BREAKFAST,
    "BikeRental": Categories.BICYCLE_RENTAL,
    "Boatstour": Categories.TOURISM_BOAT_TOURS,
    "CafeOrCoffeeShop": Categories.COFFEE_SHOP,  # predominantly coffee shops in data
    "Campground": Categories.TOURISM_CAMP_SITE,
    "Casino": Categories.CASINO,
    "Church": Categories.BUILDING_CHRISTIAN_CHURCH,
    "Cinema": Categories.CINEMA,
    "CivicStructure": Categories.GENERIC_POI,
    "ConcertHall": Categories.MUSIC_VENUE,
    "CulturalCentre": Categories.ARTS_CENTRE,
    "DaySpa": Categories.SHOP_BEAUTY_SPA,
    "DepartmentStore": Categories.SHOP_DEPARTMENT_STORE,
    "EntertainmentBusiness": Categories.EVENTS_VENUE,
    "EventVenue": Categories.EVENTS_VENUE,
    "ExerciseGym": Categories.GYM,
    "FastFoodRestaurant": Categories.FAST_FOOD,
    "FurnitureStore": Categories.SHOP_FURNITURE,
    "HolidayApartment": Categories.TOURISM_APARTMENT,
    "HolidayHouse": Categories.TOURISM_CHALET,
    "Hostel": Categories.TOURISM_HOSTEL,
    "Hotel": Categories.HOTEL,
    "Landform": Categories.NATURAL_LANDFORM,
    "LocalBusiness": Categories.GENERIC_SHOP,
    "LodgingBusiness": Categories.HOTEL,
    "Market": Categories.MARKETPLACE,
    "Monument": Categories.MONUMENT,
    "Museum": Categories.MUSEUM,
    "MusicVenue": Categories.MUSIC_VENUE,
    "NightClub": Categories.NIGHTCLUB,
    "OperaHouse": Categories.OPERA_HOUSE,
    "Park": Categories.LEISURE_PARK,
    "PerformingArtsTheater": Categories.THEATRE,
    "Place": Categories.GENERIC_POI,
    "PublicSwimmingPool": Categories.LEISURE_SWIMMING_POOL,
    "Restaurant": Categories.RESTAURANT,
    "ShoppingCenter": Categories.SHOP_MALL,
    "SportsActivityLocation": Categories.LEISURE_SPORTS_CENTRE,
    "Square": Categories.TOURISM_ATTRACTION_SQUARE,
    "Store": Categories.GENERIC_SHOP,
    "Street": Categories.TOURISM_ATTRACTION_STREET,
    "TouristAttraction": Categories.TOURISM_ATTRACTION,
    "TouristInformationCenter": Categories.TOURISM_INFORMATION,
    "Viewpoint": Categories.TOURISM_VIEWPOINT,
    "Winery": Categories.CRAFT_WINERY,
    "Zoo": Categories.TOURISM_ZOO,
}


class ZurichTourismCHSpider(Spider):
    name = "zurich_tourism_ch"
    allowed_domains = ["www.zuerich.com"]
    dataset_attributes = Licenses.CCBYSA4.value | {
        "attribution:name": "Zürich Tourism",
        "attribution:website": "https://zuerich.com",
        "attribution:wikidata": "Q139700179",
        "website": "https://www.zuerich.com/en/open-data-version-20",
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.zuerich.com/en/api/v2/data",
            callback=self.parse_feed_index,
        )

    def parse_feed_index(self, response: Response) -> AsyncIterator[Request]:
        for feed in response.json():
            if int(feed["parent"]) == 0:
                yield Request(
                    url=response.urljoin(feed["path"]),
                    callback=self.parse,
                )

    def parse(self, response: Response) -> Iterable[Feature]:
        for item in response.json():
            if coords := self.parse_coords(item):
                lat, lon = coords
            else:
                continue
            addr = item.get("address", {})
            extras = self.parse_names(item)
            name = extras.pop("name:de")
            if oh := self.parse_opening_hours(item):
                extras["opening_hours"] = oh
            website = addr.get("url")
            if website and not website.startswith("http"):
                website = None
            feature = Feature(
                ref=item["identifier"],
                lat=lat,
                lon=lon,
                name=name,
                street_address=addr.get("streetAddress"),
                postcode=addr.get("postalCode"),
                city=addr.get("addressLocality", "Zürich"),
                country=addr.get("addressCountry", "CH"),
                email=addr.get("email"),
                phone=addr.get("telephone"),
                website=website,
                image=(item.get("image") or {}).get("url"),
                extras=extras,
            )
            if category := self.parse_category(item):
                apply_category(category, feature)
            yield feature

    def parse_category(self, item: dict[str, Any]) -> Categories | None:
        c = item.get("@customType") or item.get("@type")
        if not c:
            return None
        if cat := ZURICH_TOURISM_CATEGORIES.get(c):
            return cat
        self.logger.warning(f'unknown category: "{c}"')
        return None

    @staticmethod
    def parse_coords(item: dict[str, Any]) -> Tuple[float, float] | None:
        coords = item.get("geoCoordinates") or {}
        lat, lon = coords.get("latitude"), coords.get("longitude")
        if isinstance(lat, float) and isinstance(lon, float):
            return (round(lat, 7), round(lon, 7))
        else:
            return None

    _RE_OPENING_HOURS = re.compile(r"^([A-Za-z,]+)\s+(\d{2}:\d{2}:\d{2})-(\d{2}:\d{2}:\d{2})$")

    @staticmethod
    def parse_opening_hours(item: dict[str, Any]) -> str | None:
        hours = item.get("openingHours")
        if isinstance(hours, str):
            hours = [hours]
        elif not isinstance(hours, list):
            return None
        oh = OpeningHours()
        for s in hours:
            if m := ZurichTourismCHSpider._RE_OPENING_HOURS.match(s):
                oh.add_days_range(
                    days=m.group(1).split(","),
                    open_time=m.group(2),
                    close_time=m.group(3),
                    time_format="%H:%M:%S",
                )
        return oh.as_opening_hours() or None

    @staticmethod
    def parse_names(item: dict[str, Any]) -> dict[str, str]:
        names = item.get("name") or {}
        name_de = names.get("de")
        return {
            "name:%s" % lang: name
            for (lang, name) in names.items()
            if isinstance(name, str) and (lang == "de" or name != name_de)
        }
