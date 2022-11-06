import csv
import json

import scrapy

from locations.items import GeojsonPointItem
from struct import Struct
import lzma
import base64
import h3

from locations.hex_tree import uncompress_cells

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://www.starbucks.com/bff/locations?lat={}&lng={}"


from pathlib import Path

output = Path("starbucks8")
assert output.is_dir()


class StarbucksSpider(scrapy.Spider):
    name = "starbucks"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    allowed_domains = ["www.starbucks.com"]
    download_delay = 1

    def start_requests(self):
        assert {8} == {h3.get_resolution(h) for h in res8_cells}
        for cell in res8_cells:
            p = output / f"{cell}.json"
            if p.is_file():
                continue
            # res3 = 59.8 km, 37.2 mi
            # less than the 50 mi radius of the store locator
            lat, lng = h3.cell_to_latlng(cell)
            yield scrapy.Request(
                url=STORELOCATOR.format(lat, lng),
                headers=HEADERS,
                callback=self.parse_dump,
                meta={"cell": cell},
            )

    def parse_dump(self, response):
        cell = response.meta["cell"]
        p = output / f"{cell}.json"
        p.write_text(json.dumps(response.json()))

    def parse(self, response):
        responseJson = json.loads(response.body)
        stores = responseJson["stores"]

        for store in stores:
            storeLat = store["coordinates"]["latitude"]
            storeLon = store["coordinates"]["longitude"]
            properties = {
                "name": store["name"],
                "street_address": ", ".join(
                    filter(
                        None,
                        [
                            store["address"]["streetAddressLine1"],
                            store["address"]["streetAddressLine2"],
                            store["address"]["streetAddressLine3"],
                        ],
                    )
                ),
                "city": store["address"]["city"],
                "state": store["address"]["countrySubdivisionCode"],
                "country": store["address"]["countryCode"],
                "postcode": store["address"]["postalCode"],
                "phone": store["phoneNumber"],
                "ref": store["id"],
                "lon": storeLon,
                "lat": storeLat,
                "brand": store["brandName"],
                "website": f'https://www.starbucks.com/store-locator/store/{store["id"]}/{store["slug"]}',
                "extras": {
                    "number": store["storeNumber"],
                },
            }
            yield GeojsonPointItem(**properties)

        # Get lat and lng from URL
        pairs = response.url.split("?")[-1].split("&")
        # Center is lng, lat
        center = [float(pairs[1].split("=")[1]), float(pairs[0].split("=")[1])]

        paging = responseJson["paging"]
        if paging["returned"] > 0 and paging["limit"] == paging["returned"]:
            if response.meta["distance"] > 0.15:
                nextDistance = response.meta["distance"] / 2
                # Create four new coordinate pairs
                nextCoordinates = [
                    [center[0] - nextDistance, center[1] + nextDistance],
                    [center[0] + nextDistance, center[1] + nextDistance],
                    [center[0] - nextDistance, center[1] - nextDistance],
                    [center[0] + nextDistance, center[1] - nextDistance],
                ]
                urls = [STORELOCATOR.format(c[1], c[0]) for c in nextCoordinates]
                for url in urls:
                    request = scrapy.Request(
                        url=url, headers=HEADERS, callback=self.parse
                    )
                    request.meta["distance"] = nextDistance
                    yield request


# compacted selection of 518 res2 cells known to contain search results
search_cells = uncompress_cells(
    "XQAAgAD//////////wB/6JvLAmBEHwIt0L4i/6kea1WAyGrmnCSle4J+MnaKnuO0lJ8JNW"
    "fkBgr1dN2ZteJJXCbW3bTptR3jHwRa6MuFbmPlwgc8x01eed0i8QbnFEXOtJBLQN4Re3Kk"
    "D+l9fbwgyk/Ac/UIGuMDZH7uUECakwGQRMHvgtCMw1b8sszO5+7TWF5hhzMPMh54Q9mg7i"
    "G/i6Iy1pB8dIKvhcPeNj8pH747MfGi9+Lx3N6iMu7LEUYWwrgvNq7aEJ7WP9Pk2v+lhBZI"
    "dpDVgZ6MAVDD79eyduuzOGjgqzmvfgPW0wkBIGq5bSOL1zbsBZvEMfXv/MiSl0ADgqaolS"
    "lqP9QW5i3nKaWht4oT14OcZM1rYREGzZtuiV6uJ5Ore25MbEmOCMSj0V1rSz/QM7r4yAf2"
    "0U4brV/H7BTzbhWwW+veWkbAwQ7uUrFt8YYnX4alAUE6W15a/2AolE8AMdQCWZzyC042RW"
    "pt59QNlZGr3TTNXRzc8vRTB/mRwwNppHVr/FPZAyFG9kH25BD6khEBCio/s8KjZrZuOhlZ"
    "wG3oTD9XRWX4BT6GShBl+TDmYtk4vuhtgQNWrXwwNeNRETSWVmtqsIhUhvoASBkAQ3kCPU"
    "V+xm2V8kL/jfcLUrdgRfQvtUXMkUzEpO+LNqswZot37kepBYrW4u5dWUAE7ZsvrKwSy2Ly"
    "5v1jzIIHJpmB+lyLMeVOsjkJXgfbgKb7YoGii57fjkbfutTJJqmEzpcM/Cu+H0YLdFQQ7a"
    "zLjeu93Sg8EK+q8WuTeQi45BfS1prafNqNVGM7BDBWIHQM1gTioA1xCaov/77YzVLyFzJB"
    "wrV5mc/2/vE+9jF1IXAybHlRbaDoWzRfpURYwAqZ5VHEmD6yF/eH9vuKwrF/0u5/hqU1Ty"
    "UHiV3Yl06iwmGPBXtYfKaPPUj8IPalCy5CoRdLh2yWu7l6dvZVgT9CZ/AtbsfoXgEcVozk"
    "KQtPd09ZTMRVZQ+E4mUDkl0ciQcz8nWo+gwhZAaAN8f256u+sWM1NOhrGdaRVOPXvjmF0j"
    "ZxnwF23ss5RDgd+EW7IPbKijPSAu1VBr4mmyHnmVkmT5YTEJ4DhrmI33ARyeEbufplqnO9"
    "9kB8hgknWyWj/PW1zz3gBzOMkTX2m3R+TOFJCScCC7uqi4eLziDz7WDx3gLZEAgSTB44Y3"
    "NShx9TglaAEPEC/DnSu6VwD//4tl0h"
)

# wip at res4
res4_cells = uncompress_cells(
    "XQAAgAD//////////wB/6H5Wwm80TZhOtd10pWzJPCjSPVE7V5oPE7dUDFmVN0y5U9nCed"
    "m14M6kiLUNfYGlQ4AdSn141X5M8wyxFJmpiVT0XiTtAtUob+tAiU/Sj7ZONneVeugrU4u8"
    "O9XmdwA8Fck95tlIRy3Cb7HsAAE0hMPwnKWqnpcS18K5QxLK96J4c7n3/aDDQAB4BC6OgI"
    "phIziIaFfNmPBXpUEAog0Jtovj9XDReZR5V6+Evs4WY38TgspG3vNEu/1qrmDe9NXMfHTS"
    "Qk/BFEnP8xz/L0CjQ2m+IzxAZOzD6QcmNa/uBsMej6q5NOJflo0ITqqgN1Sr+arkVtJMk9"
    "6hIcEhf9OE/91dHH3A7n+Y9x/It03v5cNIOBXoEPkZ9h6MHlZvZc1ckfI4nSeTEf9WRYlx"
    "QRmkepN6tifcoM26ePKO/Zn82PY6L7eMuFmLIi7fdqVnI/lZp3LUhrca5S50f1au+sGbpC"
    "/WPYDcwD/h6fpFaNlzZzfnBLYvZimwUDpsfN6Aa4VMHgeuxglXmOG2lUD9BY0VpEuEdxSA"
    "QSbfatGnJdoxIyIcCbZcUifEyc9X1XC9Ml0TewX/7alp/QRv+t8l4yUKef5lsjZobkQDlZ"
    "7KjlQvyjxdTE88/sU/9AcEXDf3ijJv8VClSMP6jkK53z6mtE3tgzPE6yH4uuLVIlR40JS0"
    "PUNcLi2Ob35g/pUopmwfRZcAenCTfg9S55WAAPE/msGIRhqHRuyVPnMfKZsttzgUd3bSS9"
    "IWbX6SA4sq1rV5DTn7gWabayUbeTLhZl8DBBsSq6YIJoWoJaAWHhvAclF5/xDqm6K4+2Qn"
    "iSnTnUnCEWpLpzZNVCqMw7br9zc4Bd/C91P+qTob1CwFtaK5rr5zG48gnpmTDrqMEMpSvU"
    "AjGMGUja9xhG3UdxbyrsvC4kAu56hi6WxTwf5E46Y8gKdfCVxIIVyjFa+UBQTe6j7bN41S"
    "E/cV6wcYvSwICbKwoJHHz7aK9oFpnO08Ur5WWgPmKTRpnPrDnMiRsgIav8VVoCRQ5dARoQ"
    "/sETjh6j+30rOqQuMCOgx8FY/jDuRN4u1i/LmY/Y8V/Q3U2E2Rd4P1+prQ53CtymbiG6in"
    "yOs4Tb1kQyxRgIZVCesdg8MN0Se3YST5UNzMMDMrexFRqvrDJQws+tCmy2fGAWcGXTiKYv"
    "75FL3aJhS6DHKQk9vYA2jK37UBwkBWuRium+wbPabMu/ZSQMK4w2C9qlgIgYA+Ygf4GjsV"
    "cHKeAknD1XTClWGZpDgYuE16o7n4nHsaE/OCm58l8TGqRe6CC3F8S2w3kepZO72eVXicIP"
    "UeOaPXCb+tlEl1ztXs9aFUvg8gKr76CZNtsHTzeZagjcBPDy0hWsGJpMNcfQddnTgUK+I1"
    "JXZdPS+C8DppsVB6YOXwBErjvjYNsoCScSCQ4KLryhLKdlzWPyDlyLdXuBHJOIk2X4JExo"
    "vUoomXPSzFK9fJzZZEZa+OKFyA3jkgwvzfUpB/zkNYtJigyHKKpRWHtDyaBw8osIUdDOlB"
    "ZA9n+98GMajhsI/lBREdyN5+ZT+zwAbk4Drg9FHxXaNqQDtJde1yTVSoMOHVbBwiRhkZ3f"
    "mqPm9ZFEYTE31O8/wIHKludAzgPao+14BYhIoFrcH1uNWkd7XzLWue9IcVlNXMJ/3Z+Ufu"
    "RC2LTyCxp/oM11d+RrJSxxqy2GTBruu2u0WSdY7/0U87hh9z9o3mqg28XPyHpkNUyaSEFS"
    "L9o+3TvAc254wkeDcKtpZQnufuIB4aAALYFi0RpSk4AzXokxm2GkYmf7tJF8zj6B8qbRwx"
    "DKUVevBeKMSFg0qMp2bmyrnTZNA8G4OMlSJ+knVsPl53bNpg5Vk3ZhZN+AvwLA/IvbYEKp"
    "/+TV0arPPqLSMSqW/FwqxdBfUhK8S85j8QUcIjLxuaeekOL9kjVbWqnGiT1WoVbcv8C7kU"
    "3FV1s4hI6gNxwfDlNWFIjbAPZ5/LGnqIeUetRuA3kk+bwwH/iJZZ+IGb4DL5jyb7y7pwQV"
    "5vZLaMQZqrP2hAt1LtXyVffK+xv4c9AmddcA2LYgvEcRsqf/xFsg2axrLP4ZytXoPGunXr"
    "kl970EmQ5dS1bFs3TLDu9gO5eeKZ6KL7LKfewJp2deSvbOF9s6aGPdl/RNFiP0cZZ9aYVJ"
    "rTJINFlBGb6A+sL1w65NlvFexA+sRdM4Vb8XCDSaEI3zql7uIqxAfVCfGx+AKGObsDpRUL"
    "p514mYPT13y48FSau5+32fZCwGBDro460iYv102lXU4Y90WoAiLVbeKSDHlrLQ9wgzfKZp"
    "ttkhtPuiEmItlyLL9nE63NFdliqG8F+F/PFsW3jXJsjuRj/5lAFgxOL6slHViAyKpI/d3E"
    "QPizF+satTz7jAM8JppsmJAbwfofa9JyuKDP37tJpSVq50WRg/Spwl9p8EnZyITshBxIlR"
    "nUiGL1EevFUY1ORPA5LHeY9Xiozi1B/uu8hHQQ07L1RxFNBq/uJq5zBGALICOkoluALXCB"
    "LmBygarpUaYNr04BxgiZtoWGpDcbltLhSvxGFt9E9pKCVJ2vY4G9ID7pnhx7n7RLJupBAd"
    "846BUuZBn+phV/i58XayBNv0adrfbc3L9+xYVjPfeA5FB94mQ+I+JJbZKtuR0ixWtYwoS/"
    "K9aNcREILs9Ew//zml7y"
)

# wip at res5
res5_cells = uncompress_cells(
    "XQAAgAD//////////wB/6BvSDsJ4ABfRXyts+aiGyS0peN+HAgWr+VRbA4aXkljicQXTiU"
    "QslcnZY7ORo6JVi+0mk4L02rMP3xaT4Uo8XMHuBxNrCGEra/087RyxjGHuGwV/lxNmtEm+"
    "GCiE3zHSuPaP1uVK/VArUXIJ2a2peWl62DJt7vrJ6LchgYgw3lGLy4+N3/i3vxb98Roovg"
    "i5Qsa6VaqzOYte8J0bkBaHMet0Tz/F3vFFVmcS7Z8maThTe3tNiECeqt90HlZ1FreXfYJF"
    "lNa70V0WQhploQWQjY5IcmTFbRGsppwubkJoqz/D8b2Bst5yCfrpw0rtV8Q3kWxLRaYFSU"
    "ZCS3rQInVWtRzw+exJozYcZVoTe9dP5bDYrBBTNqj7DUcvfcEYKxyFPK+NfR1oAa5T4aJP"
    "rA3cQLnNuUEUiAlTs4ic8swVSJZCjOriJE15uO38mzRSpTmys7WNdSL6QuS6PBoiuli8kp"
    "agQfgJSxwDz/Ba1SntqG3nI6Ft8NcmLTv1N67uuVrDYzMRUjBdoEGRCcNvGKl6p3e8YC18"
    "AJnjtJBvAq+M2eDAdAZgHujkgYaRcxtxmrrlnZoezsds4K2IpdR87WS8/kufEUkT89zBAp"
    "t9U+Nk0BeVgjvODOeya0gpE5JKyG6ctJrMRRJBDnuyM6mU5Z/6el2etIBR8clBrX4tb8Gv"
    "q3rKdFW6XG6+No0ra7NL/iqZKk8kWcpvKtAF5qbUvr+LPWte19MivjmpT2YFMLze5hBHJz"
    "ayYJcEGw8t93yQn2sr3dotd7CAHl57IPUeDFLqg8SoiqakTDHMsxWiTRHa6enHQmABcu+Q"
    "nf8B2RzJ8U839HJjKOAv+0f7xo9y7FhrqflTPnfsbLd/nfBO8FAPrLwV15dSeSSL0bv/Nd"
    "rE4T+36WflEB54+0Y4e62DvoMXTg8Bp/IfEFLLxRZm/+BKjuVnTxoq7VARXajtizF9t3M2"
    "LXqxY3BKc2QAFrorRchykyLbX/+l7oAA"
)

res6_cells = uncompress_cells(
    "XQAAgAD//////////wB/5//ACKXPH/5Kwf/nMm4cCc5K4dPdAUeg2lX13x1b8WJRgoU+tY"
    "eUXC5YFHTQHnSE9E18JKfBFr0ezVuHTgdqdLuPzzwO3OTDxn3f3m9I6W80cR/aX/KhEGbt"
    "+1AHl7W1VTDid07wD2ZA9jTZ4jEz9ZkGFffSnlI4gYb3DQw3WWVGOf1ndqoVtAI0AxzU6q"
    "J4rCYxHM0YXESK8QmmMRV3OeWjMxg4mmbesbgC5MQO3lse2TCsAGbkmubBVmpUztpT+u0d"
    "XZX9I6JE7SXWU7mxl1KGfOHLehApg8z6jq06YApKHuOZotFbMo3C4cO/mN8ENHaud9+hhJ"
    "NHiCq8pjLRnMVCQtoMswwC55uf+rNIzk7Ucb8IuetYhCHUqumiQPi2JAsGrEGCSVXhSErz"
    "fnKhelE0QQDLJm7pbJmYrpSnr7zbXDfgBCiDjeWxlEQIjZ4z01bR0p8Wc7m7oInuF9E1cA"
    "jo/cRk+mIKdF7srzhdjkvXfFfyprmpW4AZMQnoLF5nx4sfuZKazpm2jFp7s3wqZSah87Z2"
    "VoyY/9rZXBCQEOO2fk+Ml5AkPOVJR4gF1QU3RAopymvfe2pi10d9NioJZC56viuRCfJnsd"
    "jflndWbb7fgfVqpfl+oeYCDmF/jmBTPpEkH7hyBmEBDJPuHwFZilf/cxQLNzLT6CDdQ4N3"
    "kPVuP1Uymf55FR+a4d00JA5iLplVCpwli3RKhRiAXadIPbSKGivd1pp/il/8Oatg"
)

res7_cells = uncompress_cells(
    "XQAAgAD//////////wB/6BxSoI7fhgbYXY8yJ69Lxple/1nQ9DdFFxIu454PnwTafMOxuF"
    "xwtW1oxiT7Uvo9chQZG5cRwxrSEL9iUJ2Nlk8wWaCzf/yJna1ceqbwSXEYiZmBBdmDMqvi"
    "ZdPCvQtRWkElcn4vKTxhUAg/13ZWpvly9SiE1j5NQxUHxKfLfkSWUW0zrGPNzSYnnxzGlg"
    "AlSXW9rexc78MwIKfz/G5p3wfsVsKjc6GudDddGfVPW2nQaoZdHZlcmq1i8jr01wGc4AmT"
    "mgrC5PJjeLK5EbNOtTFYalTnmvzrDoDv9MFEEkbPIi/GuIxSJnvop+PwcrKK7BTm6sY7//"
    "+SWDqA"
)

res8_cells = uncompress_cells(
    "XQAAgAD//////////wB/4PmsAEwndOey6H6SbGkqb9Bp+hSWY2NaFjw7/U9+eCMs0ynXJU"
    "H3//5GcAA="
)

