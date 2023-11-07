# Overview

This project creates a tool for scraping infomation from job-postings on CareerBuilder, aiming to build a report bi-weekly about the labor market. The report aim to answer these questions.

- What jobs are currently in high demand?
- Are there any direct competitors currently hiring?
- What is the salary norm of the market?

# Workflow

![Alt text](figures/full-process.png)
The flow of work in this project can be found in [scraper.py](scraper.py), which contains these main function:

1. `get_soup`: Using Selenium to drive the browser.
2. `get_search_soups`: Get the html_soup of the job-searching-page
    ![Alt text](figures/work-flow1.png)
3. `extract_search_page`: Using BeautifulSoup to parse information from the html_soup
    ![Alt text](figures/work-flow2.png)
4. `extract_job_links`: Getting the soup of the job_link pages & parse data from them. 
    ![Alt text](figures/work-flow3.png)
5. `merge_search_page_n_job_link`: Merge the df_search_page with df_job_link

> The data collected then being saved as `.csv` files & being cleaned using the [cleaning.py](cleaning.py), after that, users can find the results in [EDA.ipynb ](EDA.ipynb )