import re

from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.addresses.gb.uprn_enhancer_spider import UprnEnhancerSpider

# https://www.whatdotheyknow.com/request/re_council_tax_band_data_23
# https://www.owenboswarva.com/blog/post-addr111.htm


class GbGwyneddSpider(UprnEnhancerSpider):
    name = "gb_gwynedd"
    start_urls = [
        "https://www.whatdotheyknow.com/request/re_council_tax_band_data_23/response/3478277/attach/3/Gwynedd%20domestic%20property%20list%20060626.xlsx?cookie_passthrough=1"
    ]

    ref_column = "property_ref      "
    uprn_column = "uprn        "
    address_columns = ["addr"]

    def get_regex(self) -> re.Pattern | None:
        return re.compile(
            r"^(?P<street_address>.+?)(?:, (?P<suburb>{}))?[,|\s] (?P<city>{})$".format(
                "|".join(
                    [
                        "ABERSOCH",
                        "BETHESDA",
                        "DEINIOLEN",
                        "DINAS MAWDDWY",
                        "GROESLON",
                        "LLANBEDROG",
                        "LLANBERIS",
                        "LLANRUG",
                        "MORFA NEFYN",
                        "NEFYN",
                        "PENRHOSGARNEDD",
                        "PENYGROES",
                        "TALYSARN",
                        "TREGARTH",
                        "WAUNFAWR",
                    ]
                ),
                "|".join(
                    [
                        "ABERDYFI",
                        "BALA",
                        "BANGOR",
                        "BARMOUTH",
                        "BLAENAU FFESTINIOG",
                        "CAERNARFON",
                        "CRICCIETH",
                        "DOLGELLAU",
                        "DYFFRYN ARDUDWY",
                        "FAIRBOURNE",
                        "GARNDOLBENMAEN",
                        "HARLECH",
                        "LLANBEDR",
                        "LLWYNGWRIL",
                        "MACHYNLLETH",
                        "PENRHYNDEUDRAETH",
                        "PORTHMADOG",
                        "PWLLHELI",
                        "TALSARNAU",
                        "TRAWSFYNYDD",
                        "TYWYN",
                        "Y BALA",
                        "Y FELINHELI",
                    ]
                ),
            )
        )

    def pre_process_data(self, addr: dict, **kwargs) -> None:
        addr["addr"] = (
            merge_address_lines(
                [
                    addr["addr1                              "],
                    addr["addr2                              "],
                    addr["addr3                           "],
                    addr["addr4                           "],
                ]
            )
            .removesuffix(" GWYNEDD")
            .removesuffix(" POWYS")
            .strip(" ,")
        )
