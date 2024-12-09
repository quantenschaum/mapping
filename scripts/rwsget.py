#!/usr/bin/env python3
# coding: utf-8

import sys
import json
from requests import get


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "waddenzee"

    r = get("https://www.vaarweginformatie.nl/frp/api/settings")
    r.raise_for_status()
    # print(json.dumps(r.json(), indent=2))
    path = r.json()["fddDownloadPath"]

    r = get(
        "https://www.vaarweginformatie.nl/frp/api/webcontent/downloads?pageId=infra/enc"
    )
    r.raise_for_status()
    # print(json.dumps(r.json(), indent=2))

    data = r.json()
    for e in data:
        if e["name"].lower().startswith(name):
            # print(e)
            file_id = e["fileId"]
            url = f"https://www.vaarweginformatie.nl/fdd/{path}{file_id}"
            print(url)
            break


main()
