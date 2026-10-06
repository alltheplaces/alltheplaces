import datetime
from itertools import groupby
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import bbox_contains, make_subdivisions
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

SWISS_POST = {"operator": "Die Post", "operator_wikidata": "Q614803"}
API = "https://places.post.ch/StandortSuche/StaoCacheServiceV2/api/v1"

LETTER_BOX = "T12"  # Briefeinwurf (003BE)
BRANCH = "T9"  # Filiale (001PST)
# Branch distribution types: 001F1-001F4 are branches run by Swiss Post, 001QA are "Filialen mit Partner",
# postal counters inside a partner's shop. Self-service corners and the business customer counter have none.
OWN_BRANCH_TYPES = {"001F1", "001F2", "001F3", "001F4"}
PARTNER_BRANCH_TYPE = "001QA"
COUNTER_TYPE_NORMAL = "0011"
NAME_LANGUAGE = {"GE": "fr", "VD": "fr", "NE": "fr", "JU": "fr", "TI": "it"}


class SwissPostCHSpider(Spider):
    name = "swiss_post_ch"
    item_attributes = SWISS_POST
    allowed_domains = ["places.post.ch"]

    # lon_min, lat_min, lon_max, lat_max
    CH_BOUNDS = (5.9, 45.8, 10.5, 47.9)
    # The whole country fits in one reply; a cell returning this many POIs may be truncated and is split.
    MAX_POIS = 20000
    MIN_CELL_SIZE = 0.005

    async def start(self) -> AsyncIterator[JsonRequest]:
        # "-a bounds=lon_min,lat_min,lon_max,lat_max" restricts a test run to a smaller area.
        bounds = getattr(self, "bounds", None)
        yield self.make_find_request(tuple(map(float, bounds.split(","))) if bounds else self.CH_BOUNDS)

    def make_find_request(self, bounds: tuple[float, float, float, float]) -> JsonRequest:
        extent = ",".join(str(round(c, 6)) for c in bounds)
        return JsonRequest(
            f"{API}/Find?extent={extent}&query={LETTER_BOX},{BRANCH}&clusterdist=0&agglevel=0&lod=2&lang=de"
            f"&maxpois={self.MAX_POIS}&encoding=UTF-8&autoexpand=false",
            cb_kwargs={"bounds": bounds},
            dont_filter=True,
        )

    def parse(self, response: Response, bounds: tuple[float, float, float, float]) -> Iterable[Any]:
        pois = response.json()["pois"]
        if len(pois) >= self.MAX_POIS:
            if bounds[2] - bounds[0] > self.MIN_CELL_SIZE:
                for child in make_subdivisions(bounds, 2):
                    yield self.make_find_request(child)
                return
            self.logger.warning(f"Results may be truncated in {bounds}")
            self.crawler.stats.inc_value("atp/swiss_post_ch/truncated_cell")

        for poi in pois:
            # POIs on a cell edge are collected by the neighbouring cell's query too.
            if not bbox_contains(bounds, (poi["x"], poi["y"])):
                continue
            if poi["type"] == BRANCH:
                distribution_type = poi["info"].get("DistributionType")
                if distribution_type not in OWN_BRANCH_TYPES and distribution_type != PARTNER_BRANCH_TYPE:
                    self.crawler.stats.inc_value(f"atp/swiss_post_ch/skipped_branch_type/{distribution_type}")
                    continue
            yield Request(f"{API}/Poi?id={poi['id']}", callback=self.parse_poi, cb_kwargs={"poi": poi})

    def parse_poi(self, response: Response, poi: dict) -> Iterable[Feature]:
        response.selector.remove_namespaces()
        root = response.xpath("/POI")
        item = Feature()
        item["ref"] = poi["id"]
        item["lat"] = root.xpath("GeoLocation/CoordinateLat/text()").get() or poi["y"]
        item["lon"] = root.xpath("GeoLocation/CoordinateLng/text()").get() or poi["x"]
        item["street_address"] = root.xpath("Address/Street/text()").get()
        item["postcode"] = root.xpath("Address/Zip/text()").get()
        item["city"] = root.xpath("Address/City/text()").get()
        item["state"] = root.xpath("Address/KantonCode/text()").get()
        item["country"] = root.xpath("Address/CountryCode/text()").get() or "CH"
        item["website"] = f"https://places.post.ch/de/{poi['id']}"

        if poi["type"] == LETTER_BOX:
            apply_category(Categories.POST_BOX, item)
            if collection_times := self.parse_collection_times(root.xpath('Product[@ProductTypeId="003BE_LZ"]')):
                item["extras"]["collection_times"] = collection_times
            yield item
            return

        lang = NAME_LANGUAGE.get(item["state"], "de")
        branch_name = root.xpath(f'Description[@lang="{lang}"]/text()').get() or poi["name"]
        partner_name = root.xpath('AdditionalDescription[@lang="de"]/text()').get()
        counters = root.xpath(f'Counter[@CounterTypeId="{COUNTER_TYPE_NORMAL}"]') or root.xpath("Counter")
        if counters:
            item["opening_hours"] = self.parse_opening_hours(counters[0])

        if poi["info"].get("DistributionType") == PARTNER_BRANCH_TYPE:
            # A postal counter run on behalf of Swiss Post inside a shop, bank, station etc.
            apply_category(Categories.GENERIC_POI, item)
            item["name"] = partner_name or branch_name
            item["branch"] = branch_name
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = "Die Post"
            item["extras"]["post_office:brand:wikidata"] = "Q614803"
        else:
            apply_category(Categories.POST_OFFICE, item)
            item["name"] = branch_name
        yield item

    @staticmethod
    def parse_collection_times(products) -> str | None:
        times = {}
        for deadline in products.xpath("Deadline"):
            day = int(deadline.xpath("Day/text()").get())
            time = deadline.xpath("LatestTime/text()").get()
            if not (1 <= day <= 7) or not time:
                continue
            times.setdefault(DAYS[day - 1], set()).add(time[:5])
        collection_times = []
        for time, days in groupby(DAYS, key=lambda d: ",".join(sorted(times[d])) if d in times else None):
            if time:
                days = list(days)
                collection_times.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(collection_times) or None

    @staticmethod
    def parse_opening_hours(counter) -> OpeningHours | None:
        periods = counter.xpath("OpeningPeriods")
        if not periods:
            return None
        today = datetime.date.today().isoformat()
        current = [
            p
            for p in periods
            if (p.xpath("DateFrom/text()").get() or "") <= today <= (p.xpath("DateTo/text()").get() or "9999")
        ]
        period = (current or periods)[0]
        oh = OpeningHours()
        open_days = set()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for rule in period.xpath("OpeningHours"):
            days = [DAYS[i] for i, name in enumerate(day_names) if rule.xpath(f"{name}/text()").get() == "true"]
            for timeslice in rule.xpath("Timeslice"):
                open_time = (timeslice.xpath("TimeFrom/text()").get() or "")[:5]
                close_time = (timeslice.xpath("TimeUntil/text()").get() or "")[:5]
                if open_time and close_time:
                    oh.add_days_range(days, open_time, close_time)
                    open_days.update(days)
        # The rules cover the whole week; the locator shows days without any as closed.
        oh.set_closed([day for day in DAYS if day not in open_days])
        return oh
