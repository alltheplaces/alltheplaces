from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

# Coarse (lat_min, lat_max, lon_min, lon_max) sanity boxes used to catch bad
# coordinates in the source data, keyed on the first 3 digits of the postcode.
# Metropolitan France (including Corsica) is the fallback for any other postcode.
OVERSEAS_BBOXES = {
    "971": (14.0, 18.5, -63.5, -60.5),  # Guadeloupe, Saint-Martin, Saint-Barthelemy
    "972": (14.2, 15.0, -61.3, -60.7),  # Martinique
    "974": (-21.5, -20.8, 55.0, 56.0),  # Reunion
    "976": (-13.2, -12.5, 44.9, 45.4),  # Mayotte
}
MAINLAND_BBOX = (41.0, 51.5, -5.5, 9.7)


class PromanFRSpider(Spider):
    name = "proman_fr"
    item_attributes = {"brand": "Proman", "brand_wikidata": "Q24189171", "name": "Proman"}
    allowed_domains = ["www.proman-emploi.fr"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The agency locator at https://www.proman-emploi.fr/agences is a client side
        # rendered app backed by a Magento GraphQL API. Every branch is modelled as a
        # child "category" of category id 3 ("agence").
        query = (
            '{categoryList(filters:{ids:{eq:"3"}}){children{'
            "name url_path address city zip phone email position_lat position_lng opening_time code"
            "}}}"
        )
        yield JsonRequest(url="https://www.proman-emploi.fr/graphql", data={"query": query})

    def parse(self, response: Response):
        for location in response.json()["data"]["categoryList"][0]["children"]:
            email = (location.get("email") or "").strip().lower()
            if email and not email.endswith("proman-interim.com"):
                # The locator also lists agencies of unrelated brands within the wider
                # Proman Group (Winsearch, Flexeo, Cotejob, Cordial Interim, Akuit/AGC,
                # Assistech, Impact Consulting, You.jobs) which are not Proman branded.
                continue

            item = Feature()
            item["ref"] = location["code"]
            item["branch"] = location["name"]
            item["street_address"] = location["address"]
            item["city"] = location["city"]
            item["postcode"] = (location.get("zip") or "").strip()
            item["country"] = "FR"
            item["phone"] = location.get("phone")
            item["email"] = email or None
            item["website"] = "https://www.proman-emploi.fr/" + location["url_path"]

            if (lat := location.get("position_lat")) and (lon := location.get("position_lng")):
                lat, lon = float(lat), float(lon)
                lat_min, lat_max, lon_min, lon_max = OVERSEAS_BBOXES.get(item["postcode"][:3], MAINLAND_BBOX)
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    item["lat"] = lat
                    item["lon"] = lon
                # else: source has published an implausible coordinate for this branch
                # (seen for REU41, which points to Andorra instead of La Reunion), so
                # leave coordinates blank rather than ship a wrong location.

            if opening_time := location.get("opening_time"):
                item["opening_hours"] = self.parse_opening_hours(opening_time)

            apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)

            yield item

    def parse_opening_hours(self, opening_time: str) -> OpeningHours:
        oh = OpeningHours()
        for time_range in opening_time.lower().replace(" ", "").split("/"):
            start, end = time_range.split("-")
            oh.add_days_range(DAYS_WEEKDAY, self.format_time(start), self.format_time(end))
        return oh

    @staticmethod
    def format_time(token: str) -> str:
        # Source hours are formatted like "8h00" or "14h" (implying "14h00").
        hour, _, minute = token.partition("h")
        return f"{int(hour):02d}:{minute or '00':0>2}"
