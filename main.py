import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def getProgressStatus():
    # Checking if csv file exists already or not.
    try:
        with open('progress.csv', 'r') as progress_csv:
            progress = progress_csv.readline()
            return progress.split(";")
    except:
        return []

def updateProgressStatus(state_name:str,ngo_name:str,ngo_link:str):
    # Feeding data into progress csv
    with open('progress.csv', 'w') as progress_csv:
        progress_csv.write(f"{state_name};{ngo_name};{ngo_link}")

def single_ngo_scrapper(driver: webdriver.Chrome, state_name: str, ngo_name: str, ngo_link: str) -> None:
    cur_ngo_data: dict[str, str] = {
        'State': state_name.replace(" NGOs",""),
        'NGO name': ngo_name,
        'NGO link': ngo_link,
        'Address': '',
        'PIN Code': '',
        'Phone': '',
        'Mobile': '',
        'Email': '',
        'Website': '',
        'Contact Person': '',
        'Purpose': '',
        'Aims/Objectives/Mission': '',
    }
    driver.get(ngo_link)
    all_cur_data = ""
    try:
        selector1 = 'body > div.mh-container > div.wrapper-corporate > div.mh-wrapper.clearfix > div > article > div > p:nth-child(1)'
        selector2 = 'body > div.mh-container > div.wrapper-corporate > div.mh-wrapper.clearfix > div > article > div > ul > li'
        all_cur_data = driver.find_element(By.CSS_SELECTOR, selector1).text
    except:
        try:
            all_cur_data = driver.find_element(By.CSS_SELECTOR, selector2).text
        except:
            pass
    # Scrapping only animal related NGOs
    # if 'animal' not in all_cur_data.lower():
    #     return

    all_cur_data = all_cur_data.split('\n')
    numNGOs = len(all_cur_data)
    print(f"Processing for {ngo_name} in {state_name} with {numNGOs} datapoints...")
    currentInProcess = ""
    for i in all_cur_data:
        if 'add.:' in i.lower() or 'add. :' in i.lower() or 'add :' in i.lower() or 'add:' in i.lower():
            cur_ngo_data['Address'] = i.split(':')[-1].strip()
            currentInProcess = "Address"
        elif 'pin:' in i.lower() or 'pin :' in i.lower():
            cur_ngo_data['PIN Code'] = i.split(':')[-1].strip().split(',')[0]
            currentInProcess = "PIN Code"
        elif 'phone:' in i.lower() or 'phone :' in i.lower() or 'tel :' in i.lower():
            cur_ngo_data['Phone'] = i.split(':')[-1].strip()
            currentInProcess = "Phone"
        elif 'mobile:' in i.lower() or 'mobile :' in i.lower() or 'mobile no.:' in i.lower() or 'mobile no. :' in i.lower():
            cur_ngo_data['Mobile'] = i.split(':')[-1].strip()
            currentInProcess = "Mobile"
        elif 'email:' in i.lower() or 'email :' in i.lower():
            cur_ngo_data['Email'] = i.split(':')[-1].strip()
            currentInProcess = "Email"
        elif 'website:' in i.lower() or 'website :' in i.lower():
            cur_ngo_data['Website'] = (i.split(':')[-2].strip() +":"+ i.split(':')[-1].strip()) if 'http' in i.lower() else i.split(':')[-1].strip()
            currentInProcess = "Website"
        elif 'contact person:' in i.lower() or 'contact person :' in i.lower():
            cur_ngo_data['Contact Person'] = i.split(':')[-1].strip()
            currentInProcess = "Contact Person"
        elif 'purpose:' in i.lower() or 'purpose :' in i.lower():
            cur_ngo_data['Purpose'] = i.split(':')[-1].strip()
            currentInProcess = "Purpose"
        elif 'aims/Objectives/mission:' in i.lower() or 'aims/objectives/mission :' in i.lower():
            cur_ngo_data['Aims/Objectives/Mission'] = i.split(':')[-1].strip()
            currentInProcess = "Aims/Objectives/Mission"
        else:
            if ":" not in i and len(currentInProcess) > 0:
                if currentInProcess != "PIN Code":
                    cur_ngo_data[currentInProcess] = f"{cur_ngo_data[currentInProcess]},{i.split(':')[-1].strip()}"
                if len(str(i)) == 6 and str(i).isnumeric():
                    cur_ngo_data['PIN Code'] = i.split(':')[-1].strip().split(',')[0]

    # Checking if csv file exists already or not.
    try:
        with open('output.csv', 'r') as _:
            exists = 1
    except:
        exists = 0
    # Feeding data into output csv
    with open('output.csv', 'a') as output_csv:
        csv_writer = csv.DictWriter(
            output_csv, fieldnames=list(cur_ngo_data.keys()))
        if exists == 0:
            csv_writer.writeheader()
        csv_writer.writerow(cur_ngo_data)


def single_state_scrapper(driver: webdriver.Chrome, state_name: str, state_link: str) -> None:
    # Collecting all NGO links of current state
    all_ngo_links: dict[str, str] = {}
    li: int = 1
    page: int = 1
    counter = 1
    try:
        while True:
            driver.get(str(state_link + f'?lcp_page0={page}#lcp_instance_0'))
            page += 1
            li = 1
            # Checking if current page has data or not
            # If it has no data then this will throw an exception and exit the loop
            _ = driver.find_element(
                By.CSS_SELECTOR, '#lcp_instance_0 > li:nth-child(1)')
            # Scrapping current page
            try:
                while True:
                    print(f"Finding links for {state_name} on page: {page}, total Links {counter}")
                    counter += 1
                    try:
                        cur_link: str = driver.find_element(
                            By.CSS_SELECTOR, f'#lcp_instance_0 > li:nth-child({li}) > a:nth-child(1)').get_attribute('href')
                    except:
                        cur_link: str = driver.find_element(
                            By.CSS_SELECTOR, f'#lcp_instance_0 > li:nth-child({li}) > strong:nth-child(1) > a:nth-child(1)').get_attribute('href')
                    cur_ngo_name: str = driver.find_element(
                        By.CSS_SELECTOR, f'#lcp_instance_0 > li:nth-child({li})').text
                    all_ngo_links[cur_ngo_name] = cur_link
                    li += 1
            except:
                pass
    except:
        pass

    # Scrapping each NGO one by one
    counter = 0
    numNGOs = len(all_ngo_links)
    savedState = getProgressStatus()
    savedStateRestored=False
    for i in all_ngo_links:
        counter += 1
        if not savedStateRestored:
            if len(savedState) > 0 and str(i) != savedState[1] and all_ngo_links[i] != savedState[2].replace("\n",""):
                continue
            else:
                savedStateRestored = True
        print(f"Processing for {state_name} NGO {counter} of {numNGOs} : {i}")
        updateProgressStatus(state_name,i,all_ngo_links[i])
        single_ngo_scrapper(driver, state_name, i, all_ngo_links[i])
    try:
        os.remove("progress.csv")
    except:
        pass

def main() -> None:
    # Starting up selenium web driver.
    chrome_browser_options = Options()
    chrome_browser_options.add_experimental_option(
        'useAutomationExtension', False)
    chrome_browser_options.add_experimental_option(
        'excludeSwitches', ['enable-automation'])
    chrome_browser_options.add_argument(
        '--ignore-ssl-errors=yes')
    chrome_browser_options.add_argument(
        '--ignore-certificate-errors')
    driver = webdriver.Chrome(options=chrome_browser_options)

    # Scrapping state links
    state_links: dict[str, str] = {}
    driver.get('https://ngosindia.org/')
    li: int = 1
    try:
        while True:
            try:
                cur_link: str = driver.find_element(
                    By.XPATH, f'/html/body/div[1]/div[2]/div[2]/aside/div/div/ul/li[{li}]/a').get_attribute('href')
            except:
                cur_link: str = driver.find_element(
                    By.XPATH, f'/html/body/div[1]/div[2]/div[2]/aside/div/div/ul/li[{li}]/strong/a').get_attribute('href')
            cur_state_name: str = driver.find_element(
                By.XPATH, f'/html/body/div[1]/div[2]/div[2]/aside/div/div/ul/li[{li}]').text
            state_links[cur_state_name] = cur_link
            li += 1
    except:
        pass

    # Asking the name of state to scrape
    count: int = 1
    state_names: list[str] = list(state_links.keys())
    print('Available States:')
    for i in state_names:
        print(f'    {count} == {i}')
        count += 1
    print('    0 == ALL States\n  1-3 == States from 1 to 3\n1,3,5 == States 1,3 and 5 only\n')
    to_scrape = input('Enter the number of state you want to scrape: ')
    print('Working on it...')
    restartFromSavedState = True
    if "-" not in str(to_scrape) and "," not in str(to_scrape):
        to_scrape = int(to_scrape)
        if to_scrape == 0:
            savedState = getProgressStatus()
            if len(savedState) > 0:
                restartFromSavedState = input(f'Earlier saved state found:\nState:{savedState[0]}\nNGO:{savedState[1]}\nLink:{savedState[2]}\n\nWould you like to restart from previously saved state? Default Yes. (Y/N):')
                if restartFromSavedState.lower() != "n":
                    restartFromSavedState = True
                else:
                    os.remove("progress.csv")
                    restartFromSavedState = False
            # Scrapping each state one by one
            savedStateRestored=False
            for i in state_links:
                if not savedStateRestored:
                    if restartFromSavedState and savedState[0] != str(i):
                        continue
                    else:
                        savedStateRestored = True
                single_state_scrapper(driver, i, state_links[i])
        else:
            to_scrape -= 1
            single_state_scrapper(
                driver, state_names[to_scrape], state_links[state_names[to_scrape]])
    else:
        states =[]
        if "-" in str(to_scrape):
            stateR1 = str(to_scrape).split("-")
            stateR2 = []
            for i in stateR1:
                i = int(str(i).strip())
                stateR2.append(i)
            i = stateR2[0]
            while i <= stateR2[-1]:
                states.append(i)
                i += 1

        elif "," in str(to_scrape):
            states = str(to_scrape).split(",")
        for i in states:
            i = int(str(i).strip()) - 1
            single_state_scrapper(
                driver, state_names[i], state_links[state_names[i]])

if __name__ == '__main__':
    main()
