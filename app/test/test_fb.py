"""
A simple selenium test example written by python
"""

import unittest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestTemplate(unittest.TestCase):
    """Include test cases on a given url"""

    def setUp(self):
        """Start web driver"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)

    def tearDown(self):
        """Stop web driver"""
        self.driver.quit()
        
    def test_case_1(self):
        """Find and click top-left logo button"""
        try:
            self.driver.get('https://www.facebook.com')
            print(self.driver.title)
#            el = self.driver.find_elements(By.XPATH,'.//div[@class="header__logo"]')
#            el.click()
        except NoSuchElementException as ex:
            self.fail(ex.msg)


    def test_case_2(self):
        """target username"""
        try:
            self.driver.get('https://www.facebook.com')
      #      el = self.driver.find_elements(By.XPATH,'.//div[@class="header__logo"]')
      #      el.click()
            
            username = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
            password = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
            username.clear()
            username.send_keys("goldlunge@gmail.com")
            password.clear()
            password.send_keys("Y6my@th@n")
            print("target the login button and click it")
            button = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
            
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, ".//a[@aria-label='Facebook']")))
            
            print("Element found")
        except NoSuchElementException as ex:
            self.fail(ex.msg)
            

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTemplate)
    unittest.TextTestRunner(verbosity=2).run(suite)
