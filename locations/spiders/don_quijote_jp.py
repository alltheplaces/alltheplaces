import re
from urllib.parse import parse_qs, urlsplit

import scrapy

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position, url_to_coords
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DonQuijoteJPSpider(scrapy.Spider):
    name = "don_quijote_jp"
    item_attributes = {"brand": "Don Quijote", "brand_wikidata": "Q1185381"}
    start_urls = ["https://www.donki.com/store/shop_list.php?bsns=0"]

    # The store locator at donki.com/store/shop_list.php is shared by many
    # PPIH-group store formats, not just Don Quijote. These icon classes
    # (from the "shop__icon" span next to each store name) identify a
    # genuine Don Quijote / DON DON DONKI branded store, as opposed to
    # sibling brands such as Apita, Piago, Olympic, Picasso, Times, Big
    # Save, Tokyo Central, Marukai etc. which share the same locator.
    DONKI_ICONS = {"donki", "mega", "kirakiradonki", "soradonki", "michidonki", "ekidonki", "dondon"}

    # dondondonki.com regional sites which use a consistent, easily parsed
    # "STORE NAME" / "ADDRESS" / "BUSINESS HOURS" template. The hk/mo/tw/th
    # regional sites use bespoke templates that also list non-Don-Quijote
    # tenants (sushi counters etc.) and are not covered by this spider.
    DONDONDONKI_COUNTRIES = {"sg": "SG", "my": "MY", "gu": "GU"}

    def parse(self, response):
        seen_country_urls = set()

        for store in response.xpath('//div[@class="shopList__store"]'):
            icon = (store.xpath('.//span[contains(@class,"shop__icon")]/@class').get() or "").replace(
                "shop__icon shop__icon--", ""
            )
            name = " ".join(
                store.xpath('.//h4[@class="shopList__storeName"]//span[contains(@class,"shop__name")]/text()')
                .get("")
                .split()
            )

            if icon not in self.DONKI_ICONS and not (icon == "domise" and "ドンキ" in name):
                continue

            href = store.xpath('.//ul[@class="shopList__linkBtnArea"]//a/@href').get()
            if not href:
                continue
            url = response.urljoin(href)

            if "dondondonki.com" in url:
                m = re.match(r"https?://www\.dondondonki\.com/([a-z]{2})/", url)
                if m and m.group(1) in self.DONDONDONKI_COUNTRIES and url not in seen_country_urls:
                    seen_country_urls.add(url)
                    yield scrapy.Request(
                        url,
                        callback=self.parse_dondondonki_country,
                        cb_kwargs={"country": self.DONDONDONKI_COUNTRIES[m.group(1)]},
                    )
                continue

            if "donquijotehawaii.com" in url:
                yield scrapy.Request(url, callback=self.parse_hawaii_store)
                continue

            if "shop_detail.php" in url:
                yield from self.parse_jp_store(store, name, url)

    def parse_jp_store(self, store, name, detail_url):
        shop_id = parse_qs(urlsplit(detail_url).query).get("shop_id", [None])[0]
        if not shop_id:
            return

        detail = store.xpath('.//dl[@class="shopList__shopDetail"]')

        addr_text = " ".join(
            " ".join(detail.xpath('.//dt[contains(text(),"住所")]/following-sibling::dd[1]//text()').getall()).split()
        )
        postcode = None
        if m := re.match(r"〒\s*(\d{3}-?\d{4})\s*(.*)", addr_text):
            postcode = m.group(1)
            addr_text = m.group(2).strip()

        phone = detail.xpath('.//dt[contains(text(),"TEL")]/following-sibling::dd[1]//text()').get()

        hours_text = " ".join(
            detail.xpath('.//dt[contains(text(),"営業時間")]/following-sibling::dd[1]//text()').getall()
        ).strip()
        closed_text = " ".join(
            detail.xpath('.//dt[contains(text(),"定休日")]/following-sibling::dd[1]//text()').getall()
        ).strip()

        item_fields = {
            "ref": f"jp-{shop_id}",
            "name": name,
            "addr_full": addr_text,
            "postcode": postcode,
            "phone": phone,
            "country": "JP",
            "website": detail_url,
        }

        map_url = f"https://www.donki.com/store/map.php?shop_id={shop_id}"
        yield scrapy.Request(
            map_url,
            callback=self.parse_jp_map,
            cb_kwargs={"item_fields": item_fields, "hours_text": hours_text, "closed_text": closed_text},
        )

    def parse_jp_map(self, response, item_fields, hours_text, closed_text):
        item = Feature(**item_fields)
        extract_google_position(item, response)
        self.apply_jp_hours(item, hours_text, closed_text)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item

    @staticmethod
    def apply_jp_hours(item, hours_text, closed_text):
        # Only "なし" (no closed days, i.e. open every day of the week) is
        # reliably parseable. A handful of records have garbled/duplicated
        # closed-day text (a markup quirk on a few campus stores) which is
        # left unparsed rather than guessed at.
        if closed_text and closed_text != "なし":
            return

        oh = OpeningHours()
        if hours_text.startswith("24時間"):
            oh.add_days_range(DAYS, "00:00", "23:59")
        elif m := re.match(r"(\d{1,2}:\d{2})\s*～\s*(\d{1,2}:\d{2})", hours_text):
            oh.add_days_range(DAYS, m.group(1), m.group(2))
        else:
            return
        item["opening_hours"] = oh.as_opening_hours()

    def parse_dondondonki_country(self, response, country):
        for li in response.xpath('//div[@id="storeinfoBox"]//li[@id]'):
            ref = li.xpath("./@id").get()

            name = " ".join(
                " ".join(
                    li.xpath('.//dt[contains(text(),"STORE NAME")]/following-sibling::dd[1]//text()').getall()
                ).split()
            )
            if not name:
                continue

            addr_full = " ".join(
                " ".join(
                    li.xpath('.//dt[contains(text(),"ADDRESS")]/following-sibling::dd[1]//text()').getall()
                ).split()
            )
            phone = li.xpath('.//dt[contains(text(),"PHONE NUMBER")]/following-sibling::dd[1]//text()').get()

            item_fields = {
                "ref": f"dondon-{country}-{ref}",
                "name": name,
                "addr_full": addr_full,
                "phone": phone,
                "country": country,
                "website": response.url,
            }

            map_href = li.xpath('.//div[@class="storeinfo_map"]/a/@href').get()
            if map_href:
                yield scrapy.Request(
                    response.urljoin(map_href),
                    callback=self.parse_dondondonki_map,
                    cb_kwargs={"item_fields": item_fields},
                )
            else:
                item = Feature(**item_fields)
                apply_category(Categories.SHOP_VARIETY_STORE, item)
                yield item

    def parse_dondondonki_map(self, response, item_fields):
        item = Feature(**item_fields)
        # The "GoogleMap View" link is usually a bit.ly/maps.app.goo.gl short
        # link which redirects straight to a Google Maps URL, rather than to
        # a page that itself embeds a map (so check the final response URL,
        # not just links found within the page body).
        lat, lon = url_to_coords(response.url)
        if lat is not None:
            item["lat"], item["lon"] = lat, lon
        else:
            extract_google_position(item, response)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item

    def parse_hawaii_store(self, response):
        item = Feature()
        item["ref"] = "hawaii-" + urlsplit(response.url).path.rstrip("/").rsplit("/", 1)[-1]
        item["name"] = response.xpath('normalize-space(//h1[@class="page-header"])').get()
        item["addr_full"] = " ".join(response.xpath('//div[@class="storeListAddress"]//text()').getall()).strip()
        item["addr_full"] = " ".join(item["addr_full"].split())
        item["phone"] = response.xpath('//div[@class="storeListPhone"]/a/@href').re_first(r"tel:(\+?\d+)")
        item["country"] = "US"
        item["website"] = response.url

        hours_text = " ".join(response.xpath('//div[@class="storeListStoreHours"]//text()').getall())
        if "24 hours" in hours_text.lower():
            oh = OpeningHours()
            oh.add_days_range(DAYS, "00:00", "23:59")
            item["opening_hours"] = oh.as_opening_hours()

        extract_google_position(item, response)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
