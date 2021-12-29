import re
import sys

import chardet
import requests
from bs4 import BeautifulSoup

_url = sys.argv[1]

max_len_col = 70
add_len_col = 2


def get_text_from_response(resp, replace=True):
    charset_search_headers = re.compile(r'charset=([^()<>@,;:"/[\]?.=\s]*)', re.IGNORECASE)
    charset_search_text = re.compile(
        r"<meta(?!\s*(?:name|value)\s*=)(?:[^>]*?content\s*=[\s\"']*)?([^>]*?)"
        r"[\s\"';]*charset\s*=[\s\"']*([^\s\"'/>]*)",
        re.IGNORECASE,
    )

    charset = charset_search_headers.search(resp.headers.get("content-type", ""))
    if charset and charset.groups()[0]:
        charset = charset.groups()[0]
    else:
        charset = charset_search_text.search(resp.text)
        if charset and len(charset.groups()) == 2:
            charset = charset.groups()[1]
        else:
            charset = "utf-8"

    if resp.encoding is not None:
        try:
            tmp_text = resp.text.encode(resp.encoding, "replace").decode(charset, "replace")
        except LookupError:
            try:
                charset = "utf-8"
                tmp_text = resp.text.encode(resp.encoding, "replace").decode(charset, "replace")
            except LookupError:
                charset = chardet.detect(resp.content)["encoding"]
                tmp_text = resp.content.decode(charset, "replace")

    else:
        tmp_text = resp.text

    # replace('</', ' </') needs for correct word's splitting in kw analise
    if replace:
        tmp_text = tmp_text.replace("</", " </")

    return tmp_text, charset


if not _url.startswith('http'):
    url = 'https://' + _url
else:
    url = _url

response = requests.get(url, verify=False)

_text, _ = get_text_from_response(response)
soup = BeautifulSoup(_text, features="html.parser")
for script in soup(["script", "style"]):
    script.extract()  # rip it out
text_body = soup.body.get_text() if soup.body is not None else ""
text = " ".join(text_body.split())

name = url.replace('https://', '').replace('http://', '').replace('.', '_').replace('/', '_') + '_text.txt'

with open(name, 'w', encoding='utf-8') as f:
    f.write(text)
