CLICK_OLD_DESIGN_BTN = "document.querySelector('#login_form input[type=submit]').click()"
CLICK_NEW_DESIGN_BTN = "document.querySelector('button[name=login]').click()"
CLICK_MOB_DESIGN_BTN = "document.querySelector('//button[@type='button']').click()"

XPATH_FUNC_DEF = """
function getElementByXpath(path) {
  return document.evaluate(path, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
}
"""

XPATH_CLICK = """
getElementByXpath("{0}").iterateNext().click()
"""

CLICK_POPUP_FIRST_BTN = """
getElementByXpath("//*[@id='facebook']/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div[1]/div/div[4]/div").iterateNext().click()
"""

CLICK_POPUP_SECOND_BTN = """
getElementByXpath("//*[@id='facebook']/body/div[8]/div[1]/div/div[2]/div/div/div/div/div/div[2]/div/div/div[3]/div").iterateNext().click()
"""

CLICK_POPUP_CROSS = """
document.querySelector("div [aria-label='Close Introduction']").click()
"""

CLICK_FIVE_STAR = """
getElementByXpath(".//input[@value='5']").iterateNext().click()
"""

CLICK_HELP_US_IMPROVE_SUBMIT = """
getElementByXpath("//*[@id='facebook']/body/div[9]/div[1]/div/div[2]/div/div/div/div/div[1]/div[3]/div[2]/div[2]/div").iterateNext().click()
"""