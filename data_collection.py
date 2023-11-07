import scraper as scp
# import os

# you should test first to see how many jobs are currently available
# then divided it for 50 to get the number of pages -> input that in.
# This is the test to get number of jobs ---------
# print("---This is the test to get number of jobs")
# search_soups = scp.get_search_soups(key_word='xuat-nhap-khau',
#                                     category_code='c18',
#                                     page_num=1, # scrape only 1 page to get the number of job
#                                     load_sleep_time=10,
#                                     scroll_sleep_time=1
#                                 )
# print("---Divided the number-of-jobs for 50, and round it up to get the number of pages -> input that in.")
# page_num=input()

# This is the real scrapper ---------
search_soups = scp.get_search_soups(
    key_word='xuat-nhap-khau',
    category_code='c18',
    page_num=13,
    load_sleep_time=10,
    scroll_sleep_time=1
)
# Get content of the search_pages
df_search_page = scp.extract_search_page(
    search_soups=search_soups)  # this looks good

# Get content of the job_links
df_job_link = scp.extract_job_links(df_search_page=df_search_page,
                                    load_sleep_time=10,
                                    scroll_sleep_time=1)


# Merging df_search_page & df_job_link
df_search_page.drop(['welfare', 'salary'], axis=1, inplace=True)
df_job_link.drop(['location', 'update_date', 'expire_date'],
                 axis=1, inplace=True)
# df_search_page=df_search_page[:100]
final_df = scp.merge_search_page_n_job_link(df_search_page=df_search_page,
                                            df_job_link=df_job_link)

# Saving
# print("---Please, input the file name to save the DataFrame")
# file_name=input()
final_df.to_csv('data/raw/xnk/05112023-xuat-nhap-khau.csv', index=False)
