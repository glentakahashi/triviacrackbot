#!/usr/bin/python

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def start_new_game(driver):
    new_game_btn = driver.find_element_by_css_selector('.btn-new-game')
    new_game_btn.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "btn-classic"))
    )
    class_btn = driver.find_element_by_css_selector('.btn-classic')
    class_btn.click()
    random_btn = driver.find_element_by_css_selector('.opponent-type > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > label:nth-child(1) > button:nth-child(2)')
    random_btn.click()
    play_now_btn = driver.find_element_by_css_selector('.btn-play-now')
    play_now_btn.click()

def get_answer(driver, category, spintype='CROWN'):
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
    for spin in spins:
        logger.info(spin['type'])
        if spin['type'].lower() == spintype.lower():
            questions = spin['questions']
    if category and category != 'last':
        for question in questions:
            logger.info(question['question']['category'].lower())
            if question['question']['category'].lower() == category:
                q = question['question']
    else:
        if category == 'last':
            q = questions[-1]['question']
        else:
            q = questions[0]['question']
    logger.info(q)
    return q['correct_answer']

def has_crown(driver, t=10):
    try:
        WebDriverWait(driver, t).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "choose-crown"))
        )
    except Exception:
        return False
    return True

def has_ok(driver, t=3):
    try:
        WebDriverWait(driver, t).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-ok"))
        )
    except Exception:
        return False
    return True

def has_clickable(driver, classname, t=3):
    try:
        WebDriverWait(driver, t).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "classname"))
        )
    except Exception:
        return False
    return True

def has_games(driver):
    try:
        driver.find_element_by_css_selector(".your-move-container > .panel > .list-group > div")
    except Exception:
        return False
    return True

def answer_question(driver, answer):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "question"))
    )
    time.sleep(random.triangular(2, 14, 5))
    answer_btn = driver.find_element_by_css_selector(".btn-answer:nth-child(%s)" % str(answer))
    logger.info("Answering %s " % answer_btn.text)
    answer_btn.click()
    # click continue if you succeed/fail
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-continue"))
    )
    continue_btn = driver.find_element_by_css_selector(".btn-continue")
    continue_btn.click()

def take_turn(driver):
    logger.info("Taking a turn")
    if has_ok(driver, 3):
        logger.info("Starting challenge")
        accept_btn = driver.find_element_by_css_selector(".btn-ok")
        accept_btn.click()
        categories = ['history', 'geography', 'arts', 'sports', 'entertainment', 'science']
        for category in categories:
            if random.random() < 0.84734:
                answer = int(get_answer(driver, category, 'DUEL'))+1
            else:
                logger.info("Guessing on the answer")
                answer = random.randint(1, 4)
            answer_question(driver, answer)
        try:
            # close the ad
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "modal-close"))
            )
            close_btn = driver.find_element_by_css_selector(".modal-close")
            close_btn.click()
            logger.info("lost challenge")
        except:
            logger.info("had no ad")
            pass
        if has_ok(driver, 3):
            accept_btn = driver.find_element_by_css_selector(".btn-ok")
            accept_btn.click()
            logger.info(has_clickable(driver, 'btn-answer', 3))
            if has_clickable(driver, 'btn-answer', 3):
                logger.info("Have a tiebreaker.")
                answer = int(get_answer(driver, 'last', 'DUEL'))+1
                answer_question(driver, answer)
            else:
                logger.info("Won or lost the tiebreaker")
        return
    if not has_crown(driver, 3):
        logger.info("Clicking crown")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "spin"))
        )
        # spin
        spin_btn = driver.find_element_by_css_selector(".spin")
        spin_btn.click()
    category = None
    if has_crown(driver):
        crown_btn = driver.find_element_by_css_selector(".choose-crown")
        crown_btn.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "select-category"))
        )
        # click first crown on list
        cat = driver.find_element_by_css_selector(".select-category > form > ul > li:nth-child(1) > label > input")
        category = cat.get_attribute("value")
        cat_btn = driver.find_element_by_css_selector(".select-category > form > ul > li:nth-child(1) > label > button")
        cat_btn.click()
        play_btn = driver.find_element_by_css_selector(".btn-play")
    else:
        # click play
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "play-category"))
        )
        play_btn = driver.find_element_by_css_selector(".play-category")
    logger.info("Our category is %s " % category)
    fail = False
    if random.random() < 0.84734:
        answer = int(get_answer(driver, category))+1
    else:
        fail = True
        logger.info("Guessing on the answer")
        answer = random.randint(1, 4)
    play_btn.click()
    answer_question(driver, answer)
    if not has_crown(driver, 3):
        try:
            # close the ad
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "modal-close"))
            )
            close_btn = driver.find_element_by_css_selector(".modal-close")
            close_btn.click()
            logger.info("failed a question i think")
            if fail:
                logger.info("failed on purpose though")
            else:
                logger.info("fail on accident??????")
        except:
            logger.info("had no ad")
            pass
    if has_ok(driver):
        accept_btn = driver.find_element_by_css_selector(".btn-ok")
        accept_btn.click()

def run(driver):
    # try closing a modal, say if we levelled up or something
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "modal-close"))
        )
        close_btn = driver.find_element_by_css_selector(".modal-close")
        close_btn.click()
    except:
        pass
    if "#game" in driver.current_url:
        take_turn(driver)
    else:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-new-game"))
        )
        for i in range(1, 4):
            logger.info("Checking prize %d" % i)
            prize = driver.find_element_by_css_selector('div.gacha-card:nth-child(%d)' % i)
            prize_text = driver.find_element_by_css_selector('div.gacha-card:nth-child(%d) > div:nth-child(3) > p:nth-child(1) > span:nth-child(2)' % i).text
            if prize_text.lower() == 'collect':
                logger.info("Collecting prize %d" % i)
                prize.click()
        num_lives = driver.find_element_by_css_selector('.quantity').text
        if num_lives != '0':
            logger.info("have %d lives so starting new game" % num_lives)
            start_new_game(driver)
        else:
            # if no games, sleep 5 minutes
            if has_games(driver):
                logger.info("Clicking first game")
                first_game = driver.find_element_by_css_selector(".your-move-container > .panel > .list-group > div:nth-child(1)")
                first_game.click()
            else:
                logger.info("Waiting for 5 minutes")
                time.sleep(300)
        time.sleep(random.triangular(1, 9, 3))

def start_session():
    # driver = webdriver.PhantomJS()  # or add to your PATH
    driver = webdriver.Firefox()  # or add to your PATH
    # driver.set_window_size(1024, 768)  # optional
    driver.get('https://facebook.com/')
    driver.delete_all_cookies()
    load_cookies(driver, "facebookcookies.txt", ['facebook.com', '.facebook.com'])
    driver.get('https://preguntados.com/game/')
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-fb"))
    )
    facebook_login_button = driver.find_element_by_css_selector('.btn-fb')
    facebook_login_button.click()
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-new-game"))
    )
    driver.maximize_window()
    try:
        while True:
            run(driver)
    except Exception as e:
        logger.error("failed now, at %s" % str(datetime.now()))
        logger.exception(e)
        driver.save_screenshot("screens/%s.png" % str(datetime.now()))
        #driver.quit()

if __name__ == "__main__":
    #while True:
    start_session()
