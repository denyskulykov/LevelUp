import re
from urllib.parse import urljoin
import requests
from requests.exceptions import ConnectionError
from time import time

from tools import (gen_contact_prefix, send_mail, open_output_file,
                   write_record, RE_MAIL, HEADERS, gen_mails, URL_PATHS)

from database import create_bd, insert_into_table, is_not_mail_exist

# ------------------------------ Init ------------------------------
# debug = False
debug = True
debug_limit = 10000

open_output_file()
create_bd()

start_time = time()
collection = {}
# ------------------------- Data Collection -------------------------
for base_url in URL_PATHS:
    for index in range(1, 10000):
        temp_url = urljoin(base_url, 'page-{}/'.format(index))
        response = requests.get(temp_url, headers=HEADERS, timeout=10)

        if response.status_code == 404:
            break

        body = response.content.decode()
        next_index = 0
        for _ in range(body.count('<h4 class="box-title">')):

            prefix = body.find('<h4 class="box-title">', next_index)

            start_name = body.find('a title="', prefix) + 9
            end_name = body.find('" href="', prefix)

            name = body[start_name: end_name]

            start_url = (end_name + 8)
            end_url = body.find('" target="', start_url)

            url = body[start_url: end_url]

            #
            collection.update({name: urljoin(base_url, url)})
            next_index = end_url

print(len(collection))
print('Get collection: {} seconds'.format(int(time() - start_time)))

# ------------------------- Getting Mails -------------------------

count = 0
limit = 0
for hotel in collection:
    if limit == debug_limit:
        break
    else:
        limit += 1

    info = ''
    start_sub_module = time()
    source = collection[hotel]
    response = requests.get(source, headers=HEADERS, timeout=10)

    if response.status_code != 200:
        continue

    body = response.content.decode()

    raw_mails = []
    if body.find(':</strong> <a href="') != -1:
        start = (body.find(':</strong> <a href="') + 20)
        end = body.find('" rel=', start)
        site = body[start: end]
        try:
            external_resp = requests.get(site, headers=HEADERS, timeout=10)
            site_status = external_resp.status_code
            raw_mails = re.findall(
                RE_MAIL, external_resp.content.decode('utf-8', 'ignore'))

            if not raw_mails:
                for uurl in gen_contact_prefix(site):
                    try:
                        resp_t = requests.get(uurl, headers=HEADERS, timeout=10)
                    except:
                        continue
                    if resp_t.status_code == 404:
                        continue
                    raw_mails = re.findall(
                        RE_MAIL, resp_t.content.decode('utf-8', 'ignore'))

                    if raw_mails:
                        info += 'From "/contact"; '
                        break

        except ConnectionError:
            site_status = 0
        except Exception as error:
            info += '{}; '.format(error)
            site_status = '???'
            print(error)

    else:
        site = ''
        site_status = 0

    if body.find('<span itemprop="telephone">') != -1:
        start = body.find('<span itemprop="telephone">') + 27
        end = body.find('</span>', start)
        in_phone = body[start: end] if body[start: end] else ''
    else:
        in_phone = ''

    # ------------------------- Clean data --------------------------
    hotel = hotel.split('&')[0].strip()

    if raw_mails:
        raw_mails = list(set([m.lower() for m in raw_mails]))
        display_mails = ' ;'.join(raw_mails)
    else:
        if site:
            raw_mails = (gen_mails(site))
            info += 'Generation; '
        display_mails = ''

    # ------------------------- Send Mails --------------------------
    # raw_mails = [raw_mails[0]]
    message = ''
    subject = ''

    for mail in raw_mails:
        if is_not_mail_exist(mail):
            insert_into_table(mail, hotel)

            with open('mail_message.msg', encoding='utf-8') as f:
                message = f.read().format(mail=mail, site=site)
            with open('mail_subject.msg', encoding='utf-8') as f:
                subject = f.read().format(name=hotel)

            send_mail(subject, message, '')
            info += 'Sent; '
        else:
            info += 'Exists; '

    # ------------------------ Write Record -------------------------

    # ('Name', 'Site', 'Status_Site', 'Phone', 'Mails', 'Source', 'Info')
    record = [hotel, site, site_status, in_phone,
              display_mails, source, info]
    write_record(record)

    # --------------------------- Debug -----------------------------
    count += 1
    if count % 20 == 0:
        print(count)
    else:
        if not debug:
            print('.', end='')

    if (time() - start_sub_module) > 5:
        print(site)
        print('Executed sub time: {}'.format(time() - start_sub_module))

    if debug:
        print(hotel)
        # print(source)
        print(site)
        # print(site_status)
        # print(in_phone)
        print(raw_mails)
        print(subject)
        print(message.split('\n')[0])
        # print(display_mails)
        print(info)
        print('-' * 80)


print('Execute time: {} seconds'.format(int(time() - start_time)))
print('Average value: {} seconds'.format(
    int(time() - start_time) / len(collection)))
