import requests
import configparser
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# Load the configuration
config = configparser.ConfigParser()
config.read('/home/admin-az/automation/production/meraki_mg_signal_ro/config.conf')

rsrp_threshold = float(config.get('Thresholds', 'rsrp_threshold'))
rsrq_threshold = float(config.get('Thresholds', 'rsrq_threshold'))

sender_email = config.get('Email', 'sender_email')
receiver_email = config.get('Email', 'receiver_email')
password = config.get('Email', 'password')

api_key = 'insert your api key here'
organization_id = 'insert your org id here'

headers = {
    'X-Cisco-Meraki-API-Key': api_key,
    'Content-Type': 'application/json'
}

url = f'https://api.meraki.com/api/v1/organizations/{organization_id}/cellularGateway/uplink/statuses'

alerted_serials = {}

def send_email(serial, rsrp, rsrq):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Meraki Alert: Threshold Exceeded'

    body = f'Alert: Threshold exceeded\n\nSerial Number: {serial}\nRSRP: {rsrp}\nRSRQ: {rsrq}'
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print('Email sent successfully.')
    except Exception as e:
        print(f'Error sending email: {e}')

while True:
    response = requests.get(url, headers=headers)
    data = response.json()

    for device in data:
        serial = device.get('serial', '')
        uplinks = device.get('uplinks', [])

        for uplink in uplinks:
            signal_stat = uplink.get('signalStat', {})
            rsrp = float(signal_stat.get('rsrp', 0))
            rsrq = float(signal_stat.get('rsrq', 0))

            if (rsrp < rsrp_threshold or rsrq < rsrq_threshold) and serial not in alerted_serials:
                send_email(serial, rsrp, rsrq)
                alerted_serials[serial] = datetime.now()

    # Remove serial numbers from alerted_serials after 24 hours
    current_time = datetime.now()
    serials_to_remove = [serial for serial, alert_time in alerted_serials.items() if (current_time - alert_time) > timedelta(hours=24)]
    for serial in serials_to_remove:
        del alerted_serials[serial]

    time.sleep(60)
