# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class InteriorHealthSpider(scrapy.Spider):
    name = "interior_health"
    item_attributes = {"brand": "Interior Health"}
    allowed_domains = ["www.interiorhealth.ca"]
    start_urls = [
        "https://www.interiorhealth.ca/Pages/default.aspx",
    ]
    download_delay = 0.3

    def parse(self, response):
        search_url = (
            "https://www.interiorhealth.ca/FindUs/_layouts/FindUs/By.aspx?type=Location"
        )
        yield scrapy.Request(url=search_url, callback=self.parse_location_search)

    def parse_location_search(self, response):
        # Get the view state
        view_state = response.xpath(
            '//input[@name="__VIEWSTATE"]/@value'
        ).extract_first()
        request_digest = response.xpath(
            '//input[@name="__REQUESTDIGEST"]/@value'
        ).extract_first()
        event_validation = response.xpath(
            '//input[@name="__EVENTVALIDATION"]/@value'
        ).extract_first()

        url = (
            "https://www.interiorhealth.ca/FindUs/_layouts/FindUs/By.aspx?type=Location"
        )

        headers = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Origin": "https://www.interiorhealth.ca",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://www.interiorhealth.ca/FindUs/_layouts/FindUs/By.aspx?type=Location",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
        }

        data = {
            "MSOWebPartPage_PostbackSource": "",
            "MSOTlPn_SelectedWpId": "",
            "MSOTlPn_View": "0",
            "MSOTlPn_ShowSettings": "False",
            "MSOGallery_SelectedLibrary": "",
            "MSOGallery_FilterString": "",
            "MSOTlPn_Button": "none",
            "__LASTFOCUS": "",
            "MSOSPWebPartManager_DisplayModeName": "Browse",
            "MSOSPWebPartManager_ExitingDesignMode": "false",
            "__EVENTTARGET": "ctl00$PlaceHolderMain$btnSearch",
            "__EVENTARGUMENT": "",
            "MSOWebPartPage_Shared": "",
            "MSOLayout_LayoutChanges": "",
            "MSOLayout_InDesignMode": "",
            "MSOSPWebPartManager_OldDisplayModeName": "Browse",
            "MSOSPWebPartManager_StartWebPartEditingName": "false",
            "MSOSPWebPartManager_EndWebPartEditing": "false",
            "__REQUESTDIGEST": "{0}".format(request_digest),
            "__VIEWSTATE": "{0}".format(view_state),
            "__VIEWSTATEGENERATOR": "1B0F5610",
            "__EVENTVALIDATION": "{0}".format(event_validation),
            "ctl00$PlaceHolderSearchArea$ctl00$ctl00": "Scope:Careers_WWW",
            "InputKeywords": "Search for ...",
            "ctl00$PlaceHolderSearchArea$ctl00$ctl04": "0",
            "ctl00$PlaceHolderMain$txtKeyword": "",
            "ctl00$PlaceHolderMain$ddlAndOr1": "All Location Types",
            "ctl00$PlaceHolderMain$ddlAndOr2": "All Cities",
            "__spDummyText1": "",
            "__spDummyText2": "",
        }

        yield scrapy.http.FormRequest(
            url,
            method="POST",
            headers=headers,
            formdata=data,
            callback=self.parse_location_list,
        )

    def parse_location_list(self, response):
        location_urls = response.xpath('//td[@class="alt"]/a/@href').extract()
        for location_url in location_urls:
            yield scrapy.Request(
                response.urljoin(location_url), callback=self.parse_location
            )

    def parse_location(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        state_postal = response.xpath(
            '(//td[@class="content"]/label/text())[4]'
        ).extract_first()
        state, postal = state_postal.split(" ", 1)

        properties = {
            "ref": ref,
            "name": response.xpath('//span[@class="heading1"]/text()').extract_first(),
            "addr_full": response.xpath(
                '(//td[@class="content"]/label/text())[2]'
            ).extract_first(),
            "city": response.xpath('(//td[@class="content"]/label/text())[3]')
            .extract_first()
            .strip(", "),
            "state": state,
            "postcode": postal,
            "country": "CA",
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
