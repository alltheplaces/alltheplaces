import json
import re

from scrapy.http import Request

from locations.camoufox_spider import CamoufoxSpider
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class ElysiumHealthcareSpider(CamoufoxSpider):
    name = "elysium_healthcare"
    item_attributes = {"operator": "Elysium Healthcare", "operator_wikidata": "Q39086513"}
    allowed_domains = ["www.elysiumhealthcare.co.uk"]
    start_urls = ["https://www.elysiumhealthcare.co.uk/locations/"]
    # This site is protected by a non-interactive Cloudflare Managed
    # Challenge (no clickable Turnstile widget is ever rendered). A plain
    # headless Camoufox browser clears it automatically within a few
    # seconds; the same click_solver/captcha_type machinery used for
    # interactive Turnstile elsewhere in the repo is reused here purely to
    # wait until real page content (a site-wide footer element) has
    # replaced the "Just a moment..." interstitial. The initial navigation
    # response still reports HTTP 403 even after the interstitial clears, so
    # that status has to be allowed through.
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//footer[@id="colophon"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def parse(self, response):
        urls = response.xpath('//li[@class="elementor-icon-list-item"]/a/@href').extract()

        for url in urls:
            yield Request(url=url, callback=self.parse_location)

    def parse_location(self, response):
        coming_soon = response.xpath(
            '//h1[@class="elementor-heading-title elementor-size-default"]/span/text()'
        ).extract_first()

        if not coming_soon:  # Skip empty pages
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
            name = response.xpath(
                '(//h1[@class="elementor-heading-title elementor-size-default"]/text())[2]'
            ).extract_first()

            # The address block markup is inconsistent between location
            # pages (varying levels of wrapping <div>s), so rather than
            # matching a specific structure, collect every <p> within the
            # contact block that isn't a phone/email link or one of the
            # boilerplate "Tel:"/"Email:"/referral line labels.
            contact_block = response.xpath('//div[contains(@class, "contact-link-small")]')
            addr_lines = []
            for p in contact_block.xpath(".//p"):
                if p.xpath("./a"):  # Skip phone/email link lines
                    continue
                text = "".join(p.xpath(".//text()").extract()).replace("\xa0", " ").strip()
                if not text:
                    continue
                if text.startswith(
                    ("Tel:", "T:", "Email:", "24hr referral", "Find location using what3words", "To make a referral")
                ):
                    continue
                if text.startswith("///"):  # what3words address
                    continue
                addr_lines.append(text.rstrip(","))
            address_full = ", ".join(addr_lines) if addr_lines else None

            map_settings = response.xpath('//div[contains(@id, "wpgmza_map")]/@data-settings').extract_first()
            if map_settings:
                map_data = json.loads(map_settings)
                lat = map_data["map_start_lat"]
                lon = map_data["map_start_lng"]
            else:  # No map available
                lat = ""
                lon = ""

            # Usually the phone number is a "tel:" link, but a handful of
            # pages just have plain text e.g. "T: 01582 344950" instead.
            telephone = contact_block.xpath('.//a[starts-with(@href, "tel:")]/text()').extract_first()
            if telephone:
                telephone = telephone.strip()
            else:
                for p_text in contact_block.xpath(".//p//text()").extract():
                    p_text = p_text.strip()
                    if p_text.startswith("T:"):
                        telephone = p_text.removeprefix("T:").strip()
                        break

            properties = {
                "ref": ref,
                "name": name,
                "addr_full": address_full,
                "country": "GB",
                "lat": lat,
                "lon": lon,
                "phone": telephone,
                "website": response.url,
                "extras": {},
            }

            # No clear categories can be extracted without a rewrite of this
            # spider to visit every location page. Each location page lists
            # the service(s) provided e.g.
            # - "Specialist inpatient eating disorder service"
            # - "Acute mental health service"
            # - "Neurological Rehabilitation and Complex Care"
            # Each location page also advises whether the services are
            # provided for children or adults.
            # Most locations are inpatient rehabilitation centres.
            # Just set generic "healthcare=yes" for the timebeing due to the
            # difficulty in extracting useful categories.
            properties["extras"]["healthcare"] = "yes"

            yield Feature(**properties)
