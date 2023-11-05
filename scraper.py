import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import os
import time


def get_soup(url, load_sleep_time, scroll_sleep_time):

    # Set up the driver to use a headless Chrome browser
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)

    # Load the URL in the browser and wait for the page to load
    driver.get(url)
    driver.implicitly_wait(load_sleep_time)

    # Scroll down the page to load more jobs (repeat this several times)
    for i in range(5):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_sleep_time)

    # Extract the HTML content from the fully rendered page
    html_content = driver.page_source
    driver.quit()

    # Parse the HTML content (of the searching_page) using BeautifulSoup
    html_content = BeautifulSoup(html_content, 'html.parser')

    return html_content

# soup=get_soup(url="https://careerbuilder.vn/vi/tim-viec-lam/sales-logistics.35BDC14E.html",
#               load_sleep_time=5,
#               scroll_sleep_time=1)
# print(soup.text)


def get_search_soups(key_word, category_code, page_num, load_sleep_time, scroll_sleep_time):
    """_summary_
    Get the html_soup of the job_searching_page for a specific key_word. 
    Automatically jump through all pages if the result of the searching keyword spread on multiple pages. 

    Args:
        key_word (_type_): key_word for searching jobs on the website
        category_code (_type_): this is just 1 part of the url structure when you search jobs on CareerBuilder. You should look at the source code, look at the search_url below, then then look at a real job_searching_url you'll understand.
        page_num (_type_): number of pages the key_word return on the web
        load_sleep_time (_type_): time to wait for the page to fully load its content
        scroll_sleep_time (_type_): time to wait after each scrolling down. (because some page does not automaticall load all of it's content, unless you scroll down)

    Returns:
        _bs4.BeautifulSoup_: this returns a list of html_soup of all the searching pages 
    """
    print(
        f'scrapping {page_num} searching_pages of {key_word} on CareerBuilder', flush=True)

    search_soups = []  # create an empty string to store all the infomation
    # looping through pages & getting the html soup
    for i in range(1, page_num + 1):
        search_url = f'https://careerbuilder.vn/viec-lam/{key_word}-{category_code}-trang-{i}-vi.html'

        # Get & Parse the HTML content (of the searching_page)
        search_soup = get_soup(url=search_url,
                               load_sleep_time=load_sleep_time,
                               scroll_sleep_time=scroll_sleep_time)
        search_soups.append(search_soup)

    # Print out number of currently available jobs for the searching key_word
    # `flush=True` is for printing jobs even if we are in a function.
    print(
        f"Total: {search_soups[0].find('div', class_ = 'job-found-amout').text}", flush=True)
    return search_soups


search_soups = get_search_soups(
    key_word='xuat-nhap-khau',
    category_code='c18',
    page_num=1,
    load_sleep_time=10,
    scroll_sleep_time=1
)


def extract_search_page(search_soups):
    """_summary_
    Extract information from the search_pages

    Returns:
        _pd.DataFrame_: return a df contains: 'job_link', 'job_title', 'comp_name', 'salary', 'location', 'welfare', 'expire_date', 'update_date'
    """
    support_list = []   # store data for 1 page
    for soup in search_soups:
        job_titles = soup.find_all('a', class_='job_link')
        infos = soup.find_all('div', class_='caption')
        update_dates = soup.find_all('div', class_='bottom-right-icon')
        for i, job_title in enumerate(job_titles):
            if i % 2 == 0:  # this is bc, there is a duplicate value for each `<a class="job_link"`
                # Extract job title, job_link
                job_title_text = job_title.text.strip()
                job_link = job_title.get('href')

                # Extract other job details from corresponding all_infos element (using the index `i`)
                info = infos[i//2]
                comp_name = info.find('a', class_='company-name').text.strip()
                salary = info.find('div', class_='salary').text.strip()
                expire_date = info.find(
                    'div', class_='expire-date').text.strip()

                # Extract the update_date from update_dates (using the index `i`)
                update_date = update_dates[i//2]
                update_date = re.findall('\d{2}-\d{2}-\d{4}', update_date.text)

                # All the welfares & locations are bundled together, so we have to extract them differently:
                welfares_tag = info.find('ul', class_='welfare')
                welfare = ''
                # to check if the ('ul', class_='welfare') exist
                if welfares_tag:
                    for li in welfares_tag.find_all('li'):
                        # concat text in each li tag seperated by ', '
                        welfare += li.get_text(strip=True) + ', '
                    # getting rid of the redundant ', ' at the end
                    welfare = welfare[:-2]

                locations_tag = info.find('div', class_='location')
                location = ''
                if locations_tag:
                    for li in locations_tag.find_all('li'):
                        # concat text in each li tag seperated by ', '
                        location += li.get_text(strip=True) + ', '
                    # getting rid of the redundant ', ' at the end
                    location = location[:-2]

                # Create a dictionary to store the scraped data including the job_title
                job_dict = {
                    'job_link': job_link,
                    'job_title': job_title_text,
                    'comp_name': comp_name,
                    'salary': salary,
                    'location': location,
                    'welfare': welfare,
                    'expire_date': expire_date,
                    'update_date': update_date
                }

                # Append the job dictionary to the list of jobs & then convert to dataframe
                support_list.append(job_dict)

    df_search_page = pd.DataFrame(support_list)
    return df_search_page


# ------------------------------------------------------------
# options for extract job_link w different html structure
def support_extract_job_link1(job_url, load_sleep_time, scroll_sleep_time):
    """_summary_
    Attempt 1 of getting the infos from the job_url
    """
    # Extract & Parse the HTML content using BeautifulSoup
    # job_url="https://careerbuilder.vn/vi/tim-viec-lam/data-analyst.35BD61DD.html"
    detail_soup = get_soup(url=job_url,
                           load_sleep_time=load_sleep_time,
                           scroll_sleep_time=scroll_sleep_time)

    # get the section & its children
    job_detail_content_soup = detail_soup.find(
        'section', class_='job-detail-content')
    job_desc_soup = job_detail_content_soup.find(
        'div', class_='detail-row reset-bullet')

    support_dict = {}
    # bg_blue_soup
    bg_blue_soup = job_detail_content_soup.find('div', class_='bg-blue')
    for i in bg_blue_soup.find_all('strong'):
        support_dict.update({
            i.text.strip():
                i.next_sibling.next_sibling.text.strip()
        })

    # # welfares
    # welfares_soup = job_detail_content_soup.find('div', class_='detail-row')
    # welfares_text = welfares_soup.text.strip().split(sep='\n')
    # welfares_text = [x for x in welfares_text if x != ""]
    # support_dict.update({
    #     "benefits":
    #         str(welfares_text[1:])
    # })

    # # job_desc
    # job_desc_text = job_desc_soup.text.strip()
    # support_dict.update({"job_desc": job_desc_text})

    # # job_tags, notice that, some jobs do not have job_tags
    # job_tag_soup = job_detail_content_soup.find('div', class_='job-tags')
    # if job_tag_soup == None:
    #     job_tag_text = None
    # else:
    #     # jobs-do-not-have-job-tags would make this result in errors
    #     job_tag_text = job_tag_soup.text.strip().split(sep='\n')
    #     job_tag_text = str([x for x in job_tag_text if x != ""][1:])
    # support_dict.update({
    #     "job_tags":
    #         str(job_tag_text)
    # })

    return support_dict


def support_extract_job_link2(job_url, load_sleep_time, scroll_sleep_time):
    """_summary_
    Attempt 2 of getting the infos from the job_url
    """
    detail_soup = get_soup(url=job_url,
                           load_sleep_time=load_sleep_time,
                           scroll_sleep_time=scroll_sleep_time)

    # Extracting information:
    support_dict = {}

    # [ 'Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức', 'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp']
    box_infos_soup = detail_soup.find_all('div', class_='box-info')
    for info in box_infos_soup:
        td_names = info.find_all('td', class_='name')
        for i in td_names[:7]:
            support_dict.update({i.text.strip():
                                i.find_next_sibling().text.strip()})

    # # Extracting benefits
    # welfares_soup = detail_soup.find('div', class_='detail-row box-welfares')
    # welfares_text = welfares_soup.text.strip().split(sep='\n')  # .replace('\n', ',')
    # welfares_text = str([x for x in welfares_text if x != ""][1:])
    # support_dict.update({'benefits': welfares_text})

    # # Extracting job_desc: so to make things simple. I'll store all the infor of JD in just 1 column
    # job_desc_soup = detail_soup.find('div', class_='full-content')
    # job_desc_text = job_desc_soup.text.strip().replace("\n\n", "\n")
    # support_dict.update({'job_desc': job_desc_text})
    # # support_df = pd.DataFrame(support_dict, index=[0])

    # # job_tags, notice that some jobs-do-not-have-job-tags
    # job_tag_soup = detail_soup.find('div', class_='job-tags detail-row')
    # if job_tag_soup == None:
    #     job_tag_text = None
    # else:
    #     # jobs-do-not-have-job-tags would make this result in errors
    #     job_tag_text = job_tag_soup.text.strip().split(sep='\n')
    #     job_tag_text = str([x for x in job_tag_text if x != ""][1:])
    # support_dict.update({
    #     "job_tags":
    #         str(job_tag_text)
    # })

    return support_dict


def support_extract_job_link3(job_url, load_sleep_time, scroll_sleep_time):
    # job_url="https://careerbuilder.vn/vi/tim-viec-lam/giam-doc-xuat-nhap-khau.35BDBFFA.html"
    detail_soup = get_soup(
        url=job_url, load_sleep_time=load_sleep_time, scroll_sleep_time=scroll_sleep_time)

    # Extracting information:
    support_dict = {}

    # [ 'Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức', 'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp']
    box_infos_soup = detail_soup.find(
        'div', class_='boxtp info-career', id="info-career-desktop")
    li_tags = box_infos_soup.find_all('li')
    for li in li_tags:
        text = li.text.split("\n")
        key = text[0].strip()
        content = text[1].strip()
        support_dict.update({key: content})

    # Other infos, I will update later.

    return support_dict

# job_url="https://careerbuilder.vn/vi/tim-viec-lam/giam-doc-xuat-nhap-khau.35BDBFFA.html"
# support_extract_job_link3(job_url=job_url, load_sleep_time=10, scroll_sleep_time=1)


def support_extract_job_link4(job_url, load_sleep_time, scroll_sleep_time):
    # job_url="https://careerbuilder.vn/vi/tim-viec-lam/chuyen-vien-kinh-doanh-forwarding.35BDA00A.html"
    detail_soup = get_soup(
        url=job_url, load_sleep_time=load_sleep_time, scroll_sleep_time=scroll_sleep_time)

    # Extracting information:
    support_dict = {}

    # [ 'Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức', 'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp']
    box_infos_soup = detail_soup.find(
        'div', class_='DetailJobNew', id="info-career-mb")
    # print(box_infos_soup.prettify())
    li_tags = box_infos_soup.find_all('li')
    # li_tags[7].text
    for li in li_tags[:7]:
        text = li.text.split("\n")
        key = text[1].strip()
        content = text[2].strip()
        support_dict.update({key: content})

    # Other infos, I will update later.

    return support_dict


# job_url = "https://careerbuilder.vn/vi/tim-viec-lam/chuyen-vien-kinh-doanh-forwarding.35BDA00A.html"
# support_extract_job_link4(
#     job_url=job_url, load_sleep_time=10, scroll_sleep_time=1)



def extract_job_links(df_search_page, load_sleep_time, scroll_sleep_time):
    """_summary_
    Getting infomation from the job_links. Returns a pd.DataFrame
    """
    failed_dict = {'Địa điểm': 'failed',
                   'Ngày cập nhật': 'failed',
                   'Ngành nghề': 'failed',
                   'Hình thức': 'failed',
                   'Lương': 'failed',
                   'Kinh nghiệm': 'failed',
                   'Cấp bậc': 'failed',
                   'Hết hạn nộp': 'failed',
                   'benefits': 'failed',
                   'job_desc': 'failed',
                   'job_tag': 'failed',
                   'benefit': 'failed'
                   }
    # UX/UI: getting the number of jobs processing & progression.
    num_jobs = df_search_page.job_link.shape[0]
    failed_indices = {}  # for storing failed job_link
    list_support_dict = []
    stt = 0
    for job_url in df_search_page.job_link:
        # print(job_url)
        stt += 1
        print(stt, '/', num_jobs, 'jobs scraped')
        try:
            support_dict1 = support_extract_job_link1(job_url=job_url,
                                                      load_sleep_time=load_sleep_time,
                                                      scroll_sleep_time=scroll_sleep_time)
            list_support_dict.append(support_dict1)
        except Exception as e:
            print(f"First attempt failed for {job_url}: {e}")
            try:
                support_dict = support_extract_job_link2(job_url=job_url,
                                                         load_sleep_time=load_sleep_time,
                                                         scroll_sleep_time=scroll_sleep_time)
                list_support_dict.append(support_dict)
                print("Second attempt succeed")
            except Exception as e:
                print(f"Second attempt failed for {job_url}: {e}")
                try:
                    support_dict = support_extract_job_link3(job_url=job_url,
                                                             load_sleep_time=load_sleep_time,
                                                             scroll_sleep_time=scroll_sleep_time)
                    list_support_dict.append(support_dict)
                    print("Third attempt succeed")
                except Exception as e:
                    print(f"Third attempt failed for {job_url}: {e}")
                    try:
                        support_dict = support_extract_job_link4(job_url=job_url,
                                                                 load_sleep_time=load_sleep_time,
                                                                 scroll_sleep_time=scroll_sleep_time)
                        list_support_dict.append(support_dict)
                        print("4th attempt succeed")
                    except Exception as e:
                        print(f"4th attempt failed for {job_url}: {e}")
                # only job that fail twice will be concatenated
                failed_indices.update({stt: job_url})
                list_support_dict.append(failed_dict)
                continue

    # create the df_job_link that stores infos from the job_link page
    df_job_link = pd.DataFrame()
    for i in list_support_dict:
        i_df = pd.DataFrame(data=i, index=[0])
        # axis=0 to concat vertically.
        df_job_link = pd.concat([df_job_link, i_df],
                                axis=0).reset_index(drop=True)

    # UI/UX: do some printing jobs to inform users about the process of executing the function.
    print(f'success {num_jobs - len(failed_indices)} out of {num_jobs} jobs\
        ({100 - round(len(failed_indices) * 100 / num_jobs, 2)}%)', flush=True)
    print(f'failed {len(failed_indices)} out of {num_jobs} jobs\
        ({round(len(failed_indices) * 100 / num_jobs, 2)}%)', flush=True)
    print("Failed Indices:", failed_indices)

    # cleaning detail_df
    rename_dict = {
        'Địa điểm': 'location',
        'Ngày cập nhật': 'update_date',
        'Ngành nghề': 'industry',
        'Hình thức': 'staff_type',
        'Lương': 'salary',
        'Kinh nghiệm': 'exp',
        'Cấp bậc': 'job_level',
        'Hết hạn nộp': 'expire_date'
    }
    df_job_link.columns = df_job_link.columns.str.strip()
    df_job_link = df_job_link.rename(columns=rename_dict)
    cols_for_editing = df_job_link.columns[df_job_link.columns != 'job_desc']
    df_job_link[cols_for_editing] = df_job_link[cols_for_editing].applymap(lambda x: str(x)
                                                                           .replace("['", "").replace("']", "")
                                                                           .replace('  ', '')
                                                                           .replace("'", "")
                                                                           .replace('\n', '')
                                                                           .replace('\t', '')
                                                                           .replace('\\n', '')
                                                                           .replace('\\t', '').strip()
                                                                           )
    return df_job_link


# ------------------------------------------------------------
def merge_search_page_n_job_link(df_search_page, df_job_link):
    return df_search_page.merge(df_job_link, left_index=True, right_index=True)


# -----------------------------------//-----------------------------------
# testing the function on https://careerbuilder.vn/viec-lam/Data-Analyst-k-vi.html
# search_soups = get_search_soups(key_word='data-analyst',
#                                 category_code='k',
#                                 page_num=2,
#                                 load_sleep_time=10,
#                                 scroll_sleep_time=1)
# type(search_soups[0])  # this has to be bs4.Beautifulsoup
# search_soups

# #
# df_search_page = extract_search_page(
#     search_soups=search_soups)  # this looks good
# df_search_page = df_search_page[:10].reset_index(
#     drop=True)  # reduce the df for testing

# #
# # job_url = "https://careerbuilder.vn/vi/tim-viec-lam/data-analyst.35BD57F7.html"
# # sup_dict = support_extract_job_link2(job_url=job_url)
# # pd.DataFrame(sup_dict, index=['test'])


# df_job_link = extract_job_links(df_search_page=df_search_page)
# df_job_link

# #
# merge_search_page_n_job_link(df_search_page=df_search_page,
#                              df_job_link=df_job_link) # this looks beautiful


# -----------------------------------//-----------------------------------
def get_jobs(key_word, category_code, page_num, sleep_time):
    """_summary_
    This function setting up a headless browser to surf CareerBuilder -> get html_text 
    from job_searching_page based on provided key_word -> then extracting needed information 
    from that html_text

    Args:
        key_word (_str_): a normal job_searching keyword, seperated by '-'
        page_num (_int_): number of pages of jobs that keyword has. 
                        you should try to search for the job on the page & see how many pages it has. this is to avoid pulling redundant html_text from the website. 

        sleep_time (_type_): time we wait for the page to load (depends on you internet speed)
        category_code (_str_): check for this on the website. If you're not trying to search for jobs in a specific industry, the default will be 'k'. But I do think that you should check this everytime. 
    Returns:
        a DataFrame: contains all currently available jobs of the provided keywords on CareerBuilder
    """
    ############################################################
    print(
        f'Scraping {page_num} pages of {key_word} job search on CareerBuilder from:', flush=True)
    search_soups = []  # Creating a list to store soups from all searching_pages

    # Set up the driver to use a headless Chrome browser & getting the html_text for each page
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)

    # looping through searching_pages based on the structure of the url
    for i in range(1, page_num + 1):
        # if i == 1:
        #     page_id = ''
        # else:
        #     page_id = f'-trang-{i}'
        search_url = f'https://careerbuilder.vn/viec-lam/{key_word}-{category_code}-trang-{i}-vi.html'

        # Load the URL in the browser and wait for the page to load
        driver.get(search_url)
        driver.implicitly_wait(sleep_time)

        # Scroll down the page to load more jobs (repeat this several times)
        for i in range(5):
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        # Extract the HTML content from the fully rendered page
        html_content = driver.page_source

        # Parse the HTML content (of the searching_page) using BeautifulSoup
        search_soup = BeautifulSoup(html_content, 'html.parser')

        # Append
        search_soups.append(search_soup)

    # Close the browser
    driver.quit()

    # Print out number of currently available jobs for the searching key_word
    print(
        f"     -{search_soups[0].find('div', class_ = 'job-found-amout').text} in total", flush=True)
    # `flush=True` is for printing jobs even if we are in a function.

    # total_soup IS NOT a bs4.BeautifulSoup object, but a list of bs4.BeautifulSoup objects.
    # so we have to loop through each element -> extract information from them

    ############################################################
    # Extracting information in the search_pages
    support_list1 = []   # store data for 1 page
    for search_soup in search_soups:
        # extract information from 1 page
        job_titles = search_soup.find_all('a', class_='job_link')
        infos = search_soup.find_all('div', class_='caption')
        update_dates = search_soup.find_all('div', class_='bottom-right-icon')
        for i, job_title in enumerate(job_titles):
            if i % 2 == 0:  # this is bc, there is a duplicate value for each `<a class="job_link"`
                # Extract job title, job_link
                job_title_text = job_title.text.strip()
                job_link = job_title.get('href')

                # Extract other job details from corresponding all_infos element (using the index `i`)
                info = infos[i//2]
                comp_name = info.find('a', class_='company-name').text.strip()
                salary = info.find('div', class_='salary').text.strip()
                expire_date = info.find(
                    'div', class_='expire-date').text.strip()

                # Extract the update_date from update_dates (using the index `i`)
                update_date = update_dates[i//2]
                update_date = re.findall('\d{2}-\d{2}-\d{4}', update_date.text)

                # All the welfares & locations are bundled together, so we have to extract them differently:
                welfares_tag = info.find('ul', class_='welfare')
                welfare = ''
                # to check if the ('ul', class_='welfare') exist
                if welfares_tag:
                    for li in welfares_tag.find_all('li'):
                        # concat text in each li tag seperated by ', '
                        welfare += li.get_text(strip=True) + ', '
                    # getting rid of the redundant ', ' at the end
                    welfare = welfare[:-2]

                locations_tag = info.find('div', class_='location')
                location = ''
                if locations_tag:
                    for li in locations_tag.find_all('li'):
                        # concat text in each li tag seperated by ', '
                        location += li.get_text(strip=True) + ', '
                    # getting rid of the redundant ', ' at the end
                    location = location[:-2]

                # Create a dictionary to store the scraped data including the job_title
                job_dict = {
                    'job_link': job_link,
                    'job_title': job_title_text,
                    'comp_name': comp_name,
                    'salary': salary,
                    'location': location,
                    'welfare': welfare,
                    'expire_date': expire_date,
                    'update_date': update_date
                }

                # Append the job dictionary to the list of jobs
                support_list1.append(job_dict)

    # Convert the list of job dictionaries to a pandas dataframe
    df_search_page = pd.DataFrame(support_list1)

    ############################################################
    # Extracting information in the job_link page
    df_job_link = pd.DataFrame(columns=['Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức',
                                        'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp',
                                        'Phúc lợi', 'Mô tả Công việc', 'Yêu Cầu Công Việc', 'Thông tin khác', 'Job tags / skills'])
    failed_df = pd.DataFrame([['failed'] * 13],
                             columns=['Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức',
                                      'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp',
                                      'Phúc lợi', 'Mô tả Công việc', 'Yêu Cầu Công Việc', 'Thông tin khác', 'Job tags / skills'])

    # getting the number of rows = number of jobs.
    num_jobs = df_search_page.job_link.shape[0]
    failed_indices = []  # for storing failed job_link
    stt = 0
    for job_url in df_search_page.job_link:
        stt += 1
        print(stt, '/', num_jobs, 'jobs scraped')
        try:
            ########################
            # Set up the driver to use a headless Chrome browser
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            driver = webdriver.Chrome(options=options)

            # Load the URL in the browser and wait for the page to load
            driver.get(job_url)
            driver.implicitly_wait(10)

            # Extract the HTML content from the fully rendered page
            html_content = driver.page_source
            driver.quit()

            # Parse the HTML content using BeautifulSoup
            detail_soup = BeautifulSoup(html_content, 'html.parser')

            ########################
            # Extracting information:
            # first we have to create some supporting dictionaries & lists for storing informatin
            support_dict = {}
            support_list1 = []
            support_list2 = []

            # [ 'Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức', 'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp']
            strong_tags = detail_soup.find_all('strong')
            for strong_tag in strong_tags:
                strong_parent_text = strong_tag.parent.text.strip()
                support_list1.append(strong_parent_text)
            support_list1
            for row in support_list1:
                row = row.split('\n', 1)  # split by the first '\n' character
                # now make a dict with key = row[0], values = row[1:]
                support_dict.update({row[0]: str(row[1:])})

            # ['phúc lợi', 'mô tả công việc', 'yêu cầu công việc', 'thông tin khác', 'job_tag skill'skill]
            job_detail_contents = detail_soup.find(
                'div', class_='bg-blue').find_next_siblings()
            for job_content in job_detail_contents:
                job_content = job_content.text
                support_list2.append(job_content)
            # only the first 6 elements are meaningful
            for row in support_list2[:6]:
                # split by the first 2 '\n' characters, then select from the 2nd element to the end
                row = row.split('\n', 2)[1:]
                # now make a dict with key = row[0], values = row[1:]
                support_dict.update({row[0]: str(row[1:])})

            # convert the dict to a dataframe & filter unecessaries out
            support_df = pd.DataFrame.from_dict([support_dict])
            # this support_df stores only data of 1 job
            support_df.columns = support_df.columns.str.strip()
            support_df = support_df[['Địa điểm', 'Ngày cập nhật', 'Ngành nghề', 'Hình thức',
                                     'Lương', 'Kinh nghiệm', 'Cấp bậc', 'Hết hạn nộp',
                                     'Phúc lợi', 'Mô tả Công việc', 'Yêu Cầu Công Việc', 'Thông tin khác', 'Job tags / skills']]

            # Concatenate the support_df (which stores only data of 1 job) to the detail_df
            df_job_link = pd.concat(
                [df_job_link, support_df], ignore_index=True)

        except Exception as e:
            print(f"Failed to process {job_url}: {e}")
            df_job_link = pd.concat(
                [df_job_link, failed_df], ignore_index=True)
            failed_indices.append(stt)
            continue

    # do some printing jobs to inform users about the process of executing the function.
    print(f'success {num_jobs - len(failed_indices)} jobs\
        ({100 - round(len(failed_indices) * 100 / num_jobs, 2)}%)', flush=True)
    print(f'failed to process {len(failed_indices)} out of {num_jobs} jobs\
        ({round(len(failed_indices) * 100 / num_jobs, 2)}%)', flush=True)

    # cleaning detail_df
    df_job_link.columns = ['location', 'update_date', 'industry', 'staff_type', 'salary',
                           'exp', 'job_level', 'expire_date', 'benefits', 'job_desc', 'job_require', 'other_infos', 'job_tags']
    df_job_link = df_job_link.applymap(
        lambda x: x.replace("['", "").replace("']", ""))
    df_job_link.industry = df_job_link.industry.apply(lambda x: x.replace('\\n', '').strip()
                                                      .replace('  ', '').replace('\\t', ''))
    # df_job_link[['exp', 'benefits', 'job_require', ]] = df_job_link[['exp', 'benefits', 'job_require', 'other_infos', 'job_tags']].applymap(lambda x: x.replace('\\n', '').strip()
    #                         .replace('  ', '').replace('\\t', ''))
    df_job_link

    # filter out unecessary columns
    # df_job_link = df_job_link[['industry', 'staff_type', 'exp', 'job_level']]

    ############################################################
    # Merge the detail_df (of the job_link page) to the df (of the search page)
    return df_search_page.merge(df_job_link, left_index=True, right_index=True)
    # it takes more than 5 minutes to extract details in the job_link page.
    # I wonder if I need to make this slower so the site does not see me as suspicious.

    # merged_df.to_csv(f'data/raw/{key_word}-{day}.csv', index=False)
