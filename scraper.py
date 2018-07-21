from time import time
from getpass import getpass

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup

def scrape(answer_count):
    if answer_count > 100:
        print('Quorper: WARNING, Quora feeds vary in length - sometimes less answers than 100 will be available.\nIf the program hangs on \'Loading answers\', press CTRL-C to proceed')

    loading_animation = '┐┘└┌'
    start_time = time()

    increment_size = 30/answer_count

    options = Options()
    options.add_argument('--headless')
    options.add_argument('log-level=3')
    driver = webdriver.Chrome(chrome_options=options)
    print('Quorper: Driver configured')

    driver.get('https://www.quora.com/')
    print('Quorper: Connected to Quora')

    form = driver.find_element_by_class_name('regular_login')

    email = form.find_element_by_name('email')
    email.send_keys(input('Quorper: Enter your Quora account email: - ')) 
    print('Quorper: Email sent')

    password = form.find_element_by_name('password')
    password.send_keys(getpass('Quorper: Enter your Quora account password: - '))
    print('Quorper: Password sent')

    password.send_keys(Keys.RETURN)
    print('Quorper: Credentials posted')

    print('Quorper: Waiting for redirect...')
    while not driver.title.startswith('Home') and not driver.title.startswith('('): pass

    print('Quorper: Login Successful')

    navbar = driver.find_element_by_css_selector('.SiteHeader.LoggedInSiteHeader.new_header')
    driver.execute_script('arguments[0].parentNode.removeChild(arguments[0])', navbar)

    raw_answers = []
    count = 0
    try:
        print('Quorper: Loading answers [                              ]', end='', flush=True)
        while len(raw_answers) < answer_count:
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            raw_answers = [element for element in driver.find_elements_by_class_name('Answer')]

            progbar_length = int(min(len(raw_answers), answer_count) * increment_size)
            print('\rQuorper: Loading answers [' + '#' * progbar_length + ' ' * (30 - progbar_length) + '] ' + loading_animation[count%4], end='', flush=True)
            count += 1
    except KeyboardInterrupt:
        print('\rQuorper: Loading answers [##############################]\t')
        answer_count = len(raw_answers)
        print('Quorper: Interrupt caught, proceeding with', answer_count, 'answers')

    print('\rQuorper: Loading answers [##############################]\t')
    
    loaded_answers = []
    title_list = []
    upvote_list = []

    driver.execute_script('window.scrollTo(0, 0);')

    for i in range(answer_count):
        raw_answers = [element for element in driver.find_elements_by_class_name('Answer')]
        answer = raw_answers[0]
        answer_expanded = False

        print('Quorper: Loading answer', i+1, '[EXPANDING]\t\t', end='', flush=True)
        while not answer_expanded:
            more_button = answer.find_elements_by_link_text('(more)')
            if len(more_button) > 0:
                more_button[0].click()
                print('\rQuorper: Loading answer', i+1, '[SAVING]\t\t', end='', flush=True)
            else:
                if len(answer.find_elements_by_css_selector('.AnswerFooter.ContentFooter')) > 0:
                    try:
                        upvotes = driver.find_element_by_xpath('//a[@action_click=\'AnswerUpvote\']').find_element_by_class_name('icon_action_bar-count').find_elements_by_tag_name('span')[1]
                        title = driver.execute_script('return arguments[0].parentNode.children[0]', answer).find_element_by_class_name('ui_qtext_rendered_qtext').get_attribute('innerHTML')

                        loaded_answers.append(answer.get_attribute('innerHTML'))
                        title_list.append(title)
                        upvote_list.append(upvotes.get_attribute('innerHTML'))

                        driver.execute_script('arguments[0].parentNode.parentNode.parentNode.parentNode.removeChild(arguments[0].parentNode.parentNode.parentNode)', upvotes)
                        driver.execute_script('arguments[0].parentNode.removeChild(arguments[0])', answer)
                        driver.execute_script('window.scrollTo(0, 0);')

                        answer_expanded = True

                        print('\rQuorper: Loading answer', i+1, '[DONE]\t\t')
                    except Exception as e:
                        print('\rQuorper: Loading answer', i+1, '[ERROR]\t\t', end='', flush=True)
                else:
                    more_buttons = driver.find_elements_by_class_name('more_button')
                    if len(more_buttons) > 0:
                        more_buttons[0].click()
                        driver.execute_script('arguments[0].parentNode.removeChild(arguments[0])', more_buttons[0])

    driver.close()

    processed_answers = []
    
    print('Quorper: Parsing answer data [                              ]', end='', flush=True)
    for i, answer in enumerate(loaded_answers):
        soup = BeautifulSoup(answer, 'html.parser')

        answer_body = soup.find('div', {'class': 'ui_qtext_expanded'}).findChildren()[0]

        try:
            answer_author = soup.find('a', {'class': 'user'}).decode_contents()
            answer_author_link = soup.find('a', {'class': 'user'})['href']
        except AttributeError:
            answer_author = 'Anonymous'
            answer_author_link = ''

        try:
            answer_views = soup.find('div', {'class': 'AnswerFooter ContentFooter'}).findChildren()[0].findChildren()[0].decode_contents()
        except AttributeError:
            answer_views = soup.find('div', {'class': 'ContentFooter AnswerFooter'}).findChildren()[0].findChildren()[0].decode_contents()
        if answer_views[-1] == 'k':
            answer_views = int(float(answer_views[0:-1]) * 1000)
        elif answer_views[-1] == 'm':
            answer_views = int(float(answer_views[0:-1]) * 1000000)
        elif answer_views == '':
            answer_views = 0
        else:
            answer_views = int(answer_views)

        answer_upvotes = upvote_list[i]
        if answer_upvotes[-1] == 'k':
            answer_upvotes = int(float(answer_upvotes[0:-1]) * 1000)
        elif answer_upvotes[-1] == 'm':
            answer_upvotes = int(float(answer_upvotes[0:-1]) * 1000000)
        elif answer_upvotes == '':
            answer_upvotes = 0
        else:
            answer_upvotes = int(answer_upvotes)

        answer_title = title_list[i]

        processed_answers.append({
            'title': answer_title,
            'body': answer_body,
            'author': answer_author,
            'author_link': answer_author_link,
            'views': answer_views,
            'upvotes': answer_upvotes
        })
        
        progbar_length = int((i+1) * increment_size)
        print('\rQuorper: Parsing answer data [' + '#' * progbar_length + ' ' * (30 - progbar_length) + ']', end='', flush=True)
    else:
        print()

    end_time = time()
    print('Quorper: Finished in', round(end_time-start_time), 'seconds')

    return processed_answers
