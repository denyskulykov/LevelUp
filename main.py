import re
from urllib.parse import urljoin
import requests
from requests.exceptions import ConnectionError
import urllib3
from time import time
from urllib3.exceptions import HTTPError

from database import create_bd, insert_into_table, is_not_mail_exist

from tools import (URL_PATHS,
                   RE_MAIL,
                   HEADERS,
                   contact_prefix,
                   open_output_file,
                   write_record,
                   generation_mails,
                   page_with_js,
                   send_mail,
                   check_mail,
                   gen_message_in_file
                   )

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# ------------------------------ Init ------------------------------
debug = False
# debug = True
debug_limit = 10000

open_output_file()
create_bd()

start_time = time()
collection = {}
# ------------------------- Data Collection -------------------------
for base_url in URL_PATHS:
    for index in range(1, 10000):
        temp_url = urljoin(base_url, 'page-{}/'.format(index))
        response = requests.get(temp_url, headers=HEADERS,
                                timeout=20, verify=False)

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
    try:
        response = requests.get(source, headers=HEADERS, timeout=20)
    except Exception as err:
        print(source)
        print(err)
        continue

    if response.status_code != 200:
        continue

    body = response.content.decode()

    raw_mails = []
    if body.find(':</strong> <a href="') != -1:
        start = (body.find(':</strong> <a href="') + 20)
        end = body.find('" rel=', start)
        site = body[start: end]
        try:
            external_resp = requests.get(site, headers=HEADERS, timeout=10,
                                         verify=False)
            site_status = external_resp.status_code
            external_body = external_resp.content.decode('utf-8', 'ignore')


            site_contact = ''
            if external_body.find('email-protection') != -1:
                info += 'Email-protection; '
                external_body = page_with_js(site)
                raw_mails = re.findall(RE_MAIL, external_body)
                if raw_mails:
                    info += 'JS helped; '
            else:
                raw_mails = re.findall(RE_MAIL, external_body)

            if not raw_mails:
                for uurl in contact_prefix(site):
                    try:
                        resp_t = requests.get(uurl, headers=HEADERS, timeout=10,
                                              verify=False)
                    except:
                        continue

                    if resp_t.status_code == 200:
                        site_contact = uurl
                    if resp_t.status_code == 404:
                        continue
                    resp_t = resp_t.content.decode('utf-8', 'ignore')
                    if resp_t.find('email-protection') != -1:
                        info += 'Email-protection; '
                        resp_t = page_with_js(uurl)
                        raw_mails = re.findall(RE_MAIL, resp_t)
                        if raw_mails:
                            info += 'JS helped; '
                            break
                    else:
                        raw_mails = re.findall(RE_MAIL, resp_t)

                    if raw_mails:
                        info += 'From "/contact"; '
                        break
            if not raw_mails:
                info += 'Last Run, contact - "{}"; '.format(site_contact)
                for uuurl in [site, site_contact]:
                    if not uuurl:
                        continue
                    body_l = page_with_js(uuurl)
                    raw_mails = re.findall(RE_MAIL, body_l)
                    if raw_mails:
                        info += 'JS helped; '
                        break

        except (ConnectionError, HTTPError) as error:
            site_status = 0
        except Exception as error:
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
        display_mails = ''
        # disable mail generation
        # if site:
        #     raw_mails = (generation_mails(site))
        #     info += 'Generation; '

    # ------------------------- Send Mails --------------------------
    # raw_mails = [raw_mails[0]]
    message = ''
    subject = ''

    for mail in raw_mails:
        if is_not_mail_exist(mail) and check_mail(mail):

            insert_into_table(mail, hotel)

            with open('mail_message.msg', encoding='utf-8') as f:
                message = f.read().format(mail=mail, site=site)
            with open('mail_subject.msg', encoding='utf-8') as f:
                subject = f.read().format(name=hotel)

            gen_message_in_file('{}_{}'.format(count, hotel),
                                mail, subject, message)
            # send_mail(subject, message)
            # send_mail(subject, message, mail)
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

    if (time() - start_sub_module) > 60:
        print(site)
        print('Executed sub time: {}'.format(time() - start_sub_module))

    if debug:
        print(hotel)
        print(source)
        print(site)
        print(site_status)
        print(in_phone)
        print(raw_mails)
        print(subject)
        print(message.split('\n')[0])
        print(display_mails)
        print(info)
        print('-' * 80)


print('Execute time: {} seconds'.format(int(time() - start_time)))
print('Average value: {} seconds'.format(
    int(time() - start_time) / len(collection)))
