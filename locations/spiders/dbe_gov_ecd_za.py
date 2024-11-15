import io

from openpyxl import load_workbook
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class DbeGovZASpider(Spider):
    name = "dbe_gov_ecd_za"
    download_timeout = 60

    # Link obtained from https://www.education.gov.za/Programmes/EMIS/EMISDownloads.aspx
    # It doesn't look like it can be reliably fetched if the page updates with newer data, so requires manually updating
    start_urls = [
        "https://www.education.gov.za/LinkClick.aspx?fileticket=c2vrRwdZJG8%3d&tabid=466&portalid=0&mid=10308"
    ]
    no_refs = True

    def parse(self, response):
        excel_file = response.body

        excel_data = io.BytesIO(excel_file)
        workbook = load_workbook(excel_data, read_only=True)

        sheet = workbook.active

        data = []
        for row in sheet.iter_rows(values_only=True):
            data.append(row)

        headers = data[3]
        json_data = []
        for row in data[4:]:
            json_data.append({headers[i]: cell for i, cell in enumerate(row)})

        for location in json_data:
            item = Feature()

            apply_category(Categories.KINDERGARTEN, item)

            item["lat"] = location["GIS_Lat"]
            item["lon"] = location["GIS_Long"]

            item["city"] = location["Town_City"]
            item["state"] = location["Province"]
            if location["StreetAddress"] is not None:
                item["addr_full"] = clean_address(str(location["StreetAddress"]))
            if location["PostalAddress"] is not None:
                item["extras"]["addr:postal"] = clean_address(str(location["PostalAddress"]))

            item["name"] = location["ECD_Name"]

            item["phone"] = location["Telephone"]

            yield item
