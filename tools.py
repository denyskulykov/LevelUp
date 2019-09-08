import csv
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urljoin
from config import *

# -------------------------------------------------------------------

output_file = "report/report-{date}.csv"
output_file = output_file.format(
    date=datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))

delimiter = ';'  # "," or ";"   - depend on version excel

csv_header = ('Name', 'Site', 'Status_Site',
              'Phone', 'Mails', 'Source', 'Info')
# -------------------------------------------------------------------

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/39.0.2171.95 Safari/537.36'}

RE_MAIL = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

'mailto:zzhostel@gmail.com'


def send_mail(subject, massage, mail_to_send=login):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = "{} <{}>".format(sender_name, login)
    msg['To'] = mail_to_send

    msg.attach(MIMEText(massage, 'plain'))
    try:
        s = smtplib.SMTP(host=mail_host, port=mail_port)
        s.starttls()
        s.login(login, password)
        s.send_message(msg, login, mail_to_send)
        s.quit()
    except Exception as error:
        print(error)


def open_output_file():
    with open(output_file, 'w') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=csv_header,
                                delimiter=delimiter,
                                lineterminator='\n')
        writer.writeheader()


def write_record(record):
    with open(output_file, 'a') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=csv_header,
                                delimiter=delimiter,
                                lineterminator='\n')
        try:
            writer.writerow(dict(zip(csv_header, record)))
        except Exception as error:
            print(error)


def gen_contact_prefix(url_site):
    result = []
    for sub_pr in ['', '/', '.html', '.php']:
        for pr in ['contacts', 'contact', 'kontakty']:
            result.append(urljoin(url_site, pr + sub_pr))
    for pr in ['kontaktyi', 'kontaktu', 'contact-us', 'contact_us',
               'contacts.htm', 'kontakt.html', 'hotel-contacts', 'kontakti']:
        result.append(urljoin(url_site, pr))
    return result


def gen_mails(url_site):
    result = []
    if not url_site:
        return []
    prefix = ['admin', 'info', 'booking', 'book', 'reservation', 'hotel',
              'tour', 'reception', 'office', 'marketing']
    tmp_url = url_site.replace('http://', '').replace('www.', '').split('/')[0]
    for p in prefix:
        result.append('{}@{}'.format(p, tmp_url))
    return result
