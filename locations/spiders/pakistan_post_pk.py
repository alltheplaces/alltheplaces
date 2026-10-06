import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

PAKISTAN_POST = {"operator": "Pakistan Post", "operator_wikidata": "Q4046330"}
# The source has a few points that are plainly wrong (e.g. "HYDERABAD GPO" placed in Hyderabad,
# India; latitude equal to longitude), so coordinates outside this box are dropped.
PK_BBOX = (60.8, 23.6, 77.9, 37.1)  # min lon, min lat, max lon, max lat
# The post office layer also carries administrative units without a public counter.
NON_COUNTER_UNITS = re.compile(
    r"\(Field Unit\)|^DSPS\b|^DS MST\b|District Mail Office|\bDMO\b|Postal Training Cent|Regional Director"
    r"|City Superintendent|International Mail Office",
    re.IGNORECASE,
)


class PakistanPostPKSpider(Spider):
    """
    Pakistan Post Foundation (Logistics Division) runs the Digital Franchise Post Office programme
    at dfpo.pk. Its public "Search DFPO" / "Geo Plot" pages (apply.dfpo.pk/ui/) post to a single
    endpoint with a fixed public username/key embedded in the page's JavaScript; no login is involved.
    """

    name = "pakistan_post_pk"
    item_attributes = PAKISTAN_POST
    allowed_domains = ["apply.dfpo.pk"]
    api_url = "https://apply.dfpo.pk/DAL/"
    api_auth = {"username": "dfpo.pk", "apikey": "87e8cb463421730ac871bc94cac3705f"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        # GPOs and departmental post offices. (The geo plot's DFPO layer also includes closed and
        # never-opened franchises, so DFPOs come from the registered list below instead.)
        yield JsonRequest(
            url=self.api_url,
            data={
                "process": "LIST_GEO_PLOT_LOCATIONS_FOR_DFPO_PK",
                **self.api_auth,
                "showGpo": 1,
                "showDfpo": 0,
                "showPostOffice": 1,
            },
            callback=self.parse_post_offices,
        )
        # Active Digital Franchise Post Offices, with address and city.
        yield JsonRequest(
            url=self.api_url,
            data={"process": "LIST_DFPO_LIST_FOR_DFPO_PK", **self.api_auth, "circleid": 0, "gpoid": 0, "dfpocity": ""},
            callback=self.parse_franchises,
        )

    def parse_post_offices(self, response: Response, **kwargs: Any) -> Any:
        locations = [location for location in response.json()["data"] if location["Type"] in (3, 5)]
        # GPOs (type 5) first, so the post office layer's second copies of them (type 3, "Lahore GPO")
        # are dropped as duplicates.
        locations.sort(key=lambda location: location["Type"] != 5)
        seen = set()
        for location in locations:
            name = re.sub(r"\s+", " ", location["Name"]).strip()
            if NON_COUNTER_UNITS.search(name):
                continue
            branch = re.sub(r"\s+(?:G\.?P\.?O|H\.?P\.?O|S\.?O|P\.?O)\.?$", "", name, flags=re.IGNORECASE) or name
            postcode = location["Code"] if re.fullmatch(r"\d{5}", location["Code"] or "") else None
            key = (branch.lower(), postcode)
            if key in seen:
                continue
            seen.add(key)

            item = Feature()
            item["ref"] = "{}-{}".format(location["Type"], location["Key"])
            item["branch"] = branch
            item["postcode"] = postcode
            if location["Type"] == 5:
                item["extras"]["post_office:type"] = "GPO"
            self.set_location(item, location["Lat"], location["Lng"])
            apply_category(Categories.POST_OFFICE, item)
            yield item

    def parse_franchises(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            if location["Status"] != 1:
                continue
            item = Feature()
            item["ref"] = location["DfpoId"]
            item["name"] = re.sub(r"\s+", " ", location["DfpoName"]).strip()
            item["addr_full"] = re.sub(r"\s+", " ", location["DfpoAddress"] or "").strip() or None
            item["city"] = (location["DfpoCity"] or "").strip() or None
            item["phone"] = location["ContactNumber"]
            self.set_location(item, location["DfpoLat"], location["DfpoLng"])
            apply_category(Categories.POST_OFFICE, item)
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = "Pakistan Post"
            yield item

    def set_location(self, item: Feature, lat: Any, lon: Any) -> None:
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            return
        if PK_BBOX[0] <= lon <= PK_BBOX[2] and PK_BBOX[1] <= lat <= PK_BBOX[3]:
            item["lat"], item["lon"] = lat, lon
        else:
            self.crawler.stats.inc_value("atp/{}/coordinates/out_of_bounds".format(self.name))
