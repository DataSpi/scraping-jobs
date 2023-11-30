"""
this scraper still work at 20/11/2023, but i doubt that it will
continue to work w/o modifying in the future
"""
import scraper as scp

# look at this for reference to pass data in the arguments of get_search_soup() right. 
sample_urls=[
    'https://careerbuilder.vn/viec-lam/xuat-nhap-khau-c18-vi.html', # industry Xuất nhập khẩu
    'https://careerbuilder.vn/viec-lam/van-chuyen-giao-nhan-kho-van-c33-vi.html', # industry Vận chuyển / Giao nhận / Kho vận
    'https://careerbuilder.vn/viec-lam/Data-Analyst-k-vi.html', # keyword Data-Analyst
    'https://careerbuilder.vn/viec-lam/cntt-phan-mem-c1-vi.html', # industry CNTT - Phần mềm
    'https://careerbuilder.vn/viec-lam/data-k-vi.html', # keyword data
    'https://careerbuilder.vn/viec-lam/du-lieu-k-vi.html', # keyword du-lieu
]

# get search_soup
search_soups = scp.get_search_soups(
    key_word='du-lieu',
    category_code='k',
    page_num=10,
    load_sleep_time=10,
    scroll_sleep_time=1
)
# Parsing data from the search_pages
df_search_page = scp.extract_search_page(search_soups=search_soups)


"""
for index, title in enumerate(df_search_page.job_title.tolist()): 
    print(index, title)
# after printing out the job-titles, i see that 200 is kinda the sweet spot for relevance, 
# all the jobs after the 4th page does not seem relevant to the keyword anymore. 
"""

# Scraping & parsing data from the job_links
df_job_link = scp.extract_job_links(
    df_search_page=df_search_page[:200], # all the jobs after the 4th page does not seem relevant to the keyword anymore. 
    load_sleep_time=8,
    scroll_sleep_time=1
)

# Drop unnecessaies, merging df_search_page & df_job_link
df_search_page.drop(['welfare', 'salary'], axis=1, inplace=True)
df_job_link.drop(['location', 'update_date', 'expire_date'], axis=1, inplace=True)

final_df = scp.merge_search_page_n_job_link(
    df_search_page=df_search_page,
    df_job_link=df_job_link
)

# Saving
final_df.to_csv('../data/raw/data-jobs/20231129-data-jobs.csv', index=False)
