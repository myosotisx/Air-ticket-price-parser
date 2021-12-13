from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import time
import email_client


fromCity = "北京"
toCity = "上海"

fromDates = ["2022-01-27", "2022-01-28", "2022-01-29", "2022-01-30"]
toDates = ["2022-02-06", "2022-02-05"]

notification_threshold = 2650

query_interval = 300 # sec

url_template = "https://flight.qunar.com/site/roundtrip_list_new.htm?fromCity=%s&toCity=%s&fromDate=%s&toDate=%s&fromCode=SHA&toCode=HAK&from=qunarindex&lowestPrice=null#/"

options = Options()
options.add_argument("--headless")
service = Service("./geckodriver.exe")

browser = Firefox(service=service, options=options)

# browser.implicitly_wait(5)

queries = [{"fromCity": fromCity, "toCity": toCity, "fromDate": f, "toDate": t} for t in toDates for f in fromDates]

arrival_time_begin = time.strptime("07:00", "%H:%M")
arrival_time_end = time.strptime("17:00", "%H:%M")

info_format_goback = "Go:\n  Date: %s\n  Airline: %s\n  Time: %s - %s\n  Price: %d(RMB)\nBack:\n  Date: %s\n  Airline: %s\n  Time: %s - %s\n  Price: %d(RMB)\nTotal Price: %d(RMB)\n"


email_sender = 'sthuiyi6@163.com'
email_receivers = ['sthuiyi6@163.com']

from_box = "Ticket Info Parser"
to_box = ", ".join(email_receivers)

emai_subject = "Ticket Info"

def is_transfer(ele_item):
    transfer = False
    try:
        ele_transfer = ele_item.find_element(By.XPATH, 'div[1]/div[1]/div[1]/div[2]/span')
        transfer = True if ele_transfer.text == "转" else False
    except:
        transfer = False
    return transfer

def back_cond_satisfied(ele_back_item):
    ele_arrival_time = ele_back_item.find_element(By.XPATH, 'div[1]/div[1]/div[1]/div[3]/p[1]')
    arrival_time = time.strptime(ele_arrival_time.text, "%H:%M")

    transfer = is_transfer(ele_back_item)

    return arrival_time >= arrival_time_begin and arrival_time <= arrival_time_end and not transfer

def go_cond_satisfied(ele_go_item):
    transfer = is_transfer(ele_go_item)

    return not transfer 
    
def get_satisfied_item(ele_list, cond_gen, prompt):
    idx = 0
    find_next = True
    while (find_next):
        idx += 1
        try:
            ele_item = ele_list.find_element(By.XPATH, 'div[%d]' % idx)
            find_next = not cond_gen(ele_item)
        except:
            return None
    return idx

def get_ticket_info(ele_list, index, price_offset):
    ele_item = ele_list.find_element(By.XPATH, "div[%d]" % index)

    ele_airline = ele_item.find_element(By.XPATH, "div[1]/div[1]/div[2]/span[1]")
    ele_price = ele_item.find_element(By.XPATH, "div[1]/div[2]/p[2]/span[%d]" % (1 + price_offset))

    ele_departure_time = ele_item.find_element(By.XPATH, "div[1]/div[1]/div[1]/div[1]/p[1]")
    ele_arrival_time = ele_item.find_element(By.XPATH, "div[1]/div[1]/div[1]/div[3]/p[1]")

    return ele_airline.text, int(ele_price.text), ele_departure_time.text, ele_arrival_time.text

def query(q):
    url = url_template % (q["fromCity"], q["toCity"], q["fromDate"], q["toDate"])
    print(q["fromCity"], q["toCity"], q["fromDate"], q["toDate"])
    browser.get(url)
    time.sleep(5)

    ele_go_list = browser.find_element(By.XPATH, '//*[@id="content"]/div[3]/div[2]/div[2]/div/div[1]/div/div[3]')
    ele_back_list = browser.find_element(By.XPATH, '//*[@id="content"]/div[3]/div[2]/div[2]/div/div[2]/div/div[3]')

    go_idx = get_satisfied_item(ele_go_list, go_cond_satisfied, "Go")
    back_idx = get_satisfied_item(ele_back_list, back_cond_satisfied, "Back")

    print("Go Index: %d, Back Index: %d" % (go_idx, back_idx))

    assert go_idx is not None and back_idx is not None, "Index is None"
    
    go_airline, go_price, go_departure_time, go_arrival_time = get_ticket_info(ele_go_list, go_idx, 1)
    back_airline, back_price, back_departure_time, back_arrival_time = get_ticket_info(ele_back_list, back_idx, 2)
    total_price = go_price + back_price

    res_text = info_format_goback % (q["fromDate"], go_airline, go_departure_time, go_arrival_time, go_price,
        q["toDate"], back_airline, back_departure_time, back_arrival_time, back_price,
        total_price)

    res_dict = {
        "fromDate": q["fromDate"],
        "go_airline": go_airline,
        "go_departure_time": go_departure_time, 
        "go_arrival_time": go_arrival_time, 
        "go_price": go_price,
        
        "toDate": q["toDate"],
        "back_airline": back_airline,
        "back_departure_time": back_departure_time,
        "back_arrival_time": back_arrival_time,
        "back_price": back_price,
        "total_price": total_price
    }

    return res_dict, res_text

def send_notification(res_list):
    if len(res_list) == 0:
        return

    notification_list = []
    for res in res_list:
        if res['res_dict']['total_price'] < notification_threshold:
            notification_list.append(res['res_text'])
    
    if len(notification_list) > 0:
        email_client.send_email(email_sender, email_receivers, from_box, to_box, emai_subject, '\n'.join(notification_list))

def process(retry = 3, notification = True, log_in_db = False):
    while (True):
        res_list = []
        for q in queries:
            for i in range(retry):
                try:
                    if i != 0:
                        print("Retry query", q)
                    res_dict, res_text = query(q)
                    res_list.append({ "res_dict": res_dict, "res_text": res_text })
                    print(res_text)
                    break
                except:
                    if i == retry-1:
                        print("Error happened while processing query", q)

        if notification:
            send_notification(res_list)

        time.sleep(query_interval)


if __name__ == "__main__":
    process()
    browser.quit()
