from locations.spiders.kennards_hire_au import KennardsHireAUSpider


class KennardsHireNZSpider(KennardsHireAUSpider):
    name = "kennards_hire_nz"
    allowed_domains = ["www.kennardshire.co.nz"]
    start_urls = ["https://www.kennardshire.co.nz/api/data/branches"]

    def pre_process_data(self, feature: dict) -> None:
        feature["address"].pop("state", None)
