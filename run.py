#!/usr/bin/python

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import re
import json
import random
import time

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create a file handler

handler = logging.FileHandler('triviacracker.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger

logger.addHandler(handler)

def load_cookies(driver, filename, domains):
    with open(filename, 'rb') as cookies:
        for line in cookies.readlines():
            if line is not None and line.startswith('#'):
                continue
            line = re.split('\t|\n', line)
            cookie = {
                'name': line[5],
                'value': line[6],
                'path': line[2],
                'domain': line[0],
                'secure': line[3] == 'TRUE',
                'expiry': line[4]
            }
            if cookie['domain'] in domains:
                driver.add_cookie(cookie)

def click(driver, selector):
    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    element = driver.find_element_by_css_selector(selector)
    click_element(driver, element)

def click_element(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.click(element)
    actions.perform()

def start_new_game(driver):
    if has_clickable(driver, ".btn-new-game"):
        logger.info("Clicking new game")
        click(driver, '.btn-new-game')
    else:
        raise Exception("Couldn't find new game button")
    if has_clickable(driver, ".btn-play-now"):
        click(driver, '.btn-classic')
        click(driver, '.opponent-type > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > label:nth-child(1) > button:nth-child(2)')
        click(driver, '.btn-play-now')
    else:
        raise Exception("Couldn't find a play now button")

def get_answer(driver, category, spintype):
    game_id = driver.current_url.split("#game/")[1]
    script = """
        var UserID = JSON.parse(localStorage.getItem('Preguntados/session_data')).id;
        var SessionID = JSON.parse(localStorage.getItem('Preguntados/session_data')).api_session;
        var GameID = "%s";
        var type = 'GET';

        var headers = {
            "Accept-Language": "en-US,en;q=0.8",
            "Host": "api.preguntados.com",
            "Referer": "https://preguntados.com/game/",
            "Accept-Encoding": "gzip, deflate, sdch",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0",
            "Eter-Session": "ap_session="+SessionID,
            "Origin": "https://preguntados.com",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json; charset=utf-8",
            "Eter-Agent": "1|Web-FB|Chrome 39.0.2171.65|0|Windows|0|1.1|en|en||1",
            "etergames-referer": "true"
        };

        var queryString = "?_=" + encodeURIComponent(new Date().getTime());

        var url = "https://api.preguntados.com/api/users/" + UserID + "/games/" + GameID + queryString;

        return $.ajax({
            type: type,
            url: url,
            headers: headers,
            async: false
        }).responseText; """ % game_id
    data = driver.execute_script(script)
    spins = json.loads(data)['spins_data']['spins']
    questions = spins[0]['questions']
    logger.debug("Looking for spintype %s" % spintype)
    for spin in spins:
        logger.debug("Found spintype %s" % spin['type'])
        if spin['type'].lower() == spintype.lower():
            questions = spin['questions']
            logger.debug("Found correct spin: %s" % questions)
    if category and category != 'last':
        logger.debug("Searching for category %s in questions" % category)
        for question in questions:
            logger.debug("Found question category %s" % question['question']['category'].lower())
            if question['question']['category'].lower() == category:
                q = question['question']
                logger.debug("Found correct question: %s" % q)
    else:
        if category == 'last':
            q = questions[-1]['question']
            logger.debug("Returning last question of spin, likely a tiebreaker: %s" % q)
        else:
            q = questions[0]['question']
            logger.debug("Returning first question of spin: %s" % q)
    if random.random() > 0.85734:
        logger.info("Choosing a random answer instead of correct answer")
        return random.randint(1, 4)
    return int(q['correct_answer']) + 1

def has_crown(driver, t=5):
    return has_clickable(driver, ".choose-crown", t)

def has_ok(driver):
    return has_clickable(driver, ".btn-ok", 3)

def has_games(driver):
    return has_clickable(driver, ".your-move-container > .panel > .list-group > div")

def has_answer(driver):
    return has_clickable(driver, ".btn-answer", 3)

def has_element(driver, selector, t=10):
    logger.debug("Checking for %s" % selector)
    try:
        WebDriverWait(driver, t).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except Exception:
        logger.debug("Didn't find %s" % selector)
        return False
    logger.debug("Found %s" % selector)
    return True

def has_clickable(driver, selector, t=10):
    logger.debug("Checking for clickable %s" % selector)
    try:
        WebDriverWait(driver, t).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
    except Exception:
        logger.debug("Didn't find clickable %s" % selector)
        return False
    logger.debug("Found clickable %s" % selector)
    return True

def answer_question(driver, category, spintype, playbutton=None):
    if playbutton:
        click_element(driver, playbutton)
    if not has_answer(driver):
        raise Exception("No question found")
    answer = get_answer(driver, category, spintype)
    time.sleep(random.triangular(2, 14, 5))
    answer_btn = driver.find_element_by_css_selector(".btn-answer:nth-child(%s)" % str(answer))
    logger.info("Answering %s" % answer_btn.text)
    click_element(driver, answer_btn)
    driver.save_screenshot("screens/question %s.png" % str(datetime.now()))
    # click continue if you succeed/fail
    if has_clickable(driver, '.btn-continue'):
        logger.debug("Clicking continue")
        click(driver, '.btn-continue')
    else:
        raise Exception("Couldn't find continue button")

def close_or_ok_modal(driver):
    if has_element(driver, ".modal"):
        if has_clickable(driver, ".modal-close", 3):
            logger.debug("Clicking modal close")
            click(driver, '.modal-close')
        elif has_ok(driver):
            logger.debug("Clicking modal OK")
            click(driver, '.btn-ok')
        else:
            driver.save_screenshot("screens/modal %s.png" % str(datetime.now()))
            logger.info("Found modal without an OK or a close button")

def take_challenge(driver):
    logger.info("Starting challenge")
    close_or_ok_modal(driver)
    categories = ['history', 'geography', 'arts', 'sports', 'entertainment', 'science']
    for category in categories:
        answer_question(driver, category, 'DUEL')
    # You should have an OK button after duel
    if has_ok(driver):
        close_or_ok_modal(driver)
        # If we got another question, its a tiebreaker
        if has_answer(driver):
            logger.info("Have a tiebreaker.")
            answer_question(driver, 'last', 'DUEL')
        else:
            logger.info("Won or lost the tiebreaker")
        # May have a "you've won" and an ad
        close_or_ok_modal(driver)
        close_or_ok_modal(driver)

def take_crown_turn(driver):
    logger.info("Taking a crown turn")
    click(driver, '.choose-crown')
    if has_element(driver, '.select-category'):
        # get the first crown's title
        cat = driver.find_element_by_css_selector(".select-category > form > ul > li:nth-child(1) > label > input")
        category = cat.get_attribute("value")
        # click first crown on list
        click(driver, '.select-category > form > ul > li:nth-child(1) > label > button')
        playbutton = driver.find_element_by_css_selector(".btn-play")
        answer_question(driver, category, 'CROWN', playbutton)
    else:
        raise Exception("Couldn't find the crown select menu after clicking crown")
    close_or_ok_modal(driver)

def take_turn(driver):
    logger.info("Taking a turn")
    if has_crown(driver):
        take_crown_turn(driver)
        return
    if has_ok(driver):
        take_challenge(driver)
        return
    if has_clickable(driver, '.spin'):
        logger.info("Spinning")
        click(driver, '.spin')
    else:
        raise Exception("Expected to find spin button but didn't")
    if has_crown(driver, 10):
        take_crown_turn(driver)
        return
    if has_clickable(driver, '.play-category'):
        logger.info("Clicking play")
        playbutton = driver.find_element_by_css_selector(".play-category")
        answer_question(driver, None, 'NORMAL', playbutton)
    else:
        raise Exception("Couldn't find play button")
    if has_crown(driver):
        take_crown_turn(driver)
        return
    close_or_ok_modal(driver)

def collect_prizes(driver, num_lives):
    if has_clickable(driver, '.btn-omit'):
        logger.info("Skipping gacha tutorial")
        click(driver, '.btn-omit')
    collected_lives = False
    for i in range(1, 4):
        logger.info("Checking prize %d" % i)
        if has_clickable(driver, 'div.gacha-card:nth-child(%d)' % i):
            prize = driver.find_element_by_css_selector('div.gacha-card:nth-child(%d)' % i)
            prize_text = driver.find_element_by_css_selector('div.gacha-card:nth-child(%d) > div:nth-child(3) > p:nth-child(1) > span:nth-child(2)' % i).text
            if prize_text.lower() == 'collect':
                prize_icon = driver.find_element_by_css_selector('div.gacha-card:nth-child(%d) > div:nth-child(1) > div.icon' % i)
                # check if we have hearts
                if collected_lives or "lives" in prize_icon.get_attribute("class") and num_lives != '0':
                    logger.info("Skipping clicking prize because it is extra hearts and we are not empty on hearts")
                    continue
                if "lives" in prize_icon.get_attribute("class"):
                    collected_lives = True
                logger.info("Collecting prize %d" % i)
                click_element(driver, prize)
        else:
            logger.error("Couldn't find gacha card %d" % i)

def run(driver):
    logger.info("Running")
    if "#game" in driver.current_url:
        take_turn(driver)
    elif "#dashboard" in driver.current_url:
        # try closing a modal, say if we levelled up or something
        close_or_ok_modal(driver)
        num_lives = driver.find_element_by_css_selector('.quantity').text
        collect_prizes(driver, num_lives)
        if num_lives != '0' and has_clickable(driver, '.btn-new-game'):
            logger.info("have %s lives so starting new game" % num_lives)
            start_new_game(driver)
        else:
            if has_games(driver):
                logger.info("Clicking first game")
                click(driver, '.your-move-container > .panel > .list-group > div:nth-child(1)')
            else:
                logger.info("Waiting for 5 minutes")
                time.sleep(300)
                logger.info("Refreshing the page")
                driver.refresh()
    else:
        raise Exception("Got to page we don't recognize: %s" % driver.current_url)
    time.sleep(random.triangular(1, 9, 3))

def start_session():
    logger.info("Starting a new session")
    driver = webdriver.Firefox()
    driver.maximize_window()
    logger.info("Loading facebook")
    driver.get('https://facebook.com/')
    logger.info("Facebook loaded")
    driver.delete_all_cookies()
    try:
        load_cookies(driver, "facebookcookies.txt", ['facebook.com', '.facebook.com'])
    except Exception as e:
        logger.error("Couldn't set cookies, probably wrong domain")
        driver.quit()
        raise
    logger.info("Loading Trivia Crack")
    driver.get('https://preguntados.com/game/')
    logger.info("Trivia Crack Loaded")
    if has_clickable(driver, '.btn-fb', 120):
        logger.info("Clicking facebook login button")
        click(driver, '.btn-fb')
    else:
        raise Exception("Could not find facebook login button")
    close_or_ok_modal(driver)
    if has_clickable(driver, '.btn-new-game', 30):
        try:
            while True:
                run(driver)
        except Exception as e:
            logger.error("Failed at %s" % str(datetime.now()))
            logger.exception(e)
            driver.save_screenshot("screens/%s.png" % str(datetime.now()))
            driver.quit()
    else:
        logger.error("Couldn't find new_game button")
        logger.error("Failed at %s" % str(datetime.now()))
        driver.save_screenshot("screens/%s.png" % str(datetime.now()))
        driver.quit()

if __name__ == "__main__":
    while True:
        try:
            start_session()
        except Exception as e:
            logger.error("Somehow failed start_session")
            logger.exception(e)
            time.sleep(300)
