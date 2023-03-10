from datetime import datetime
import peewee
from playhouse.db_url import connect
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# устанавливаем соединение с базой данных
db = connect('postgresql://aliyar:1@localhost:5432/selenium')
db.connect()


# создаем модель для таблицы с объявлениями
class Listing(peewee.Model):
    image_url = peewee.CharField()
    date = peewee.DateField()
    price = peewee.DecimalField()

    class Meta:
        database = db
        table_name = 'listings'


# создаем экземпляр браузера
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
driver = webdriver.Chrome(options=options)
num_pages = 1
try:
    num_pages_str = driver.find_element(By.CSS_SELECTOR, "span.showing-count").text
    num_pages = int(num_pages_str.split("of")[-1].strip()) // 20 + 1
except:
    pass
# перебираем все страницы с объявлениями
for page_num in range(1, num_pages + 1):    # открываем страницу с объявлениями
    url = f"https://www.kijiji.ca/b-apartments-condos/city-of-toronto/page-{page_num}/c37l1700273"
    driver.get(url)

    # ждем, пока загрузится список объявлений
    wait = WebDriverWait(driver, 10)
    ads = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.info-container")))

    # перебираем все объявления
    for ad in ads:
        try:
            # получаем URL изображения
            image_url = ad.find_element(By.TAG_NAME, "img").get_attribute("src")
        except:
            image_url = ""

        # получаем дату
        date = "картинки нету"
        try:
            date_str = ad.find_element(By.CLASS_NAME, "date-posted").text
            if "ago" in date_str:
                date = ""
            else:
                date = datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
            date = 'not date'

        # получаем цену
        try:
            price_str = ad.find_element(By.CSS_SELECTOR, "div.price").text
            price = float(price_str.replace(',', '').replace('$', '').strip())
        except:
            price = None

        print("Изображение:", image_url)
        print("Дата:", date.strftime('%d-%m-%Y') if date else "")
        print("Цена:", "$" + str(price) if price else "")
        print("===================")

        if date and price:
            listing = Listing(image_url=image_url, date=date, price=price)
            listing.save()

# закрываем браузер
driver.quit()
