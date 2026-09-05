import re

import chompjs
from scrapy import Spider, signals
from scrapy.exceptions import DontCloseSpider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class YaokoJPSpider(Spider):
    """Extract Yaoko (JP) store details from the official main website.

    Coords are not present on the main site, so the job board is crawled first
    to build a ``branch -> (lat, lon)`` map, then the main site's store list is
    crawled and each store is enriched with coordinates by matching branch name.

    One caveat is job board doesn't always return all sotres and changes time by time. So we only fill the coords with stores which publish at least one job posting as best effort.
    """

    name = "yaoko_jp"
    item_attributes = {
        "brand": "ヤオコー",
        "brand_wikidata": "Q11344967",
    }

    start_urls = ["https://yaoko-job.net/jobfind-pc/area/All"]
    store_list_url = "https://www.yaoko-net.com/store/"

    branch_to_coords_map: dict[str, tuple[float, float]] = {}
    seen_job_stores: set[str] = set()
    phase2_started = False

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.handle_idle, signal=signals.spider_idle)
        return spider

    def parse(self, response: Response):
        next_page = response.xpath("//a[contains(@href, '?page=') and contains(., '次へ')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        job_postings = response.xpath("//article[contains(@class, 'multiple_standard')]//div[contains(@class,'box')]")
        for job_posting in job_postings:
            store_name = job_posting.xpath("normalize-space(.//h2/a/text())").get()
            if not store_name:
                continue
            parts = store_name.split()
            branch = parts[1] if len(parts) > 1 else store_name
            key = self.branch_key(branch)
            if key in self.seen_job_stores:
                continue
            self.seen_job_stores.add(key)

            website = response.urljoin(job_posting.xpath(".//h2/a/@href").get())
            yield Request(f"{website}/map", callback=self.parse_job_map, cb_kwargs={"key": key})

    def handle_idle(self):
        # Coords come from the job board (phase 1), not the main site (phase 2).
        # Scrapy runs requests concurrently with no ordering, so without this
        # gate the store crawl would start before ``branch_to_coords_map`` is fully
        # built and most stores would silently get no coords. ``spider_idle`` called
        # only once phase 1 is complete, so we start phase 2 exactly then.
        if not self.phase2_started:
            self.phase2_started = True
            self.crawler.engine.crawl(Request(self.store_list_url, callback=self.parse_store_list))
            raise DontCloseSpider

    def parse_job_map(self, response: Response, key: str):
        coords = self.extract_json(response)
        self.branch_to_coords_map[key] = (coords["latitude"], coords["longitude"])

    def parse_store_list(self, response: Response):
        seen: set[str] = set()
        for url in response.xpath("//a[contains(@href, '/store/store') and contains(@href, '.html')]/@href").getall():
            url = response.urljoin(url)
            if url in seen:
                continue
            seen.add(url)
            yield Request(url, callback=self.parse_store)

    def parse_store(self, response: Response):
        rows = response.xpath("//table[contains(@class, 'store_info_table')]//tr")
        info = {
            label: value
            for tr in rows
            if (label := tr.xpath("./th/text()").get(""))
            for value in [tr.xpath("string(./td)").get("")]
        }

        item = Feature()
        item["ref"] = response.url.rstrip("/").split("/")[-1].replace(".html", "")
        item["branch"] = re.sub(r"（.*?）$", "", response.xpath("//h1/text()").get("")).strip()
        item["website"] = response.url
        item["country"] = "JP"

        addr_lines = [line.strip() for line in info.get("住所", "").split("\n") if line.strip()]
        item["addr_full"] = re.sub(r"〒\s*[0-9\-]+\s*", "", "\n".join(addr_lines)).strip()
        postcode = re.search(r"〒\s*([0-9\-]+)", info.get("住所", ""))
        if postcode:
            item["postcode"] = postcode.group(1)
        item["phone"] = info.get("電話番号", "").strip()
        item["opening_hours"] = self.parse_hours(info.get("営業時間", "").strip())

        coords = self.branch_to_coords_map.get(self.branch_key(item["branch"]))
        if coords:
            item["lat"], item["lon"] = coords

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    @staticmethod
    def branch_key(name: str) -> str:
        return re.sub(r"[（(][^）)]*[）)]$", "", name).strip()

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        oh = OpeningHours()
        line = re.sub(r"\s", "", text.replace("：", ":").replace("～", "-").replace("〜", "-"))
        m = re.search(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", line)
        if m:
            oh.add_days_range(DAYS, m.group(1), m.group(2))
        return oh

    def extract_json(self, response: Response) -> dict:
        script = response.xpath("//script[contains(., 'createGoogleMaps')]/text()").get()
        blob = re.search(r"createGoogleMaps\(\s*(\{.*?\})\s*\)", script or "", re.S).group(1)
        return chompjs.parse_js_object(blob)
