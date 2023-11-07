import scraper as scp

# look at this for reference to pass data in the arguments of get_search_soup() right. 
sample_urls=[
    'https://careerbuilder.vn/viec-lam/xuat-nhap-khau-c18-vi.html', # industry Xuất nhập khẩu
    'https://careerbuilder.vn/viec-lam/van-chuyen-giao-nhan-kho-van-c33-vi.html', # industry Vận chuyển / Giao nhận / Kho vận
    'https://careerbuilder.vn/viec-lam/Data-Analyst-k-vi.html', # keyword Data-Analyst
    'https://careerbuilder.vn/viec-lam/cntt-phan-mem-c1-vi.html', # industry CNTT - Phần mềm
]

# get search_soup
search_soups = scp.get_search_soups(
    key_word='van-chuyen-giao-nhan-kho-van',
    category_code='c33',
    page_num=13,
    load_sleep_time=10,
    scroll_sleep_time=1
)
# Parsing data from the search_pages
df_search_page = scp.extract_search_page(search_soups=search_soups)

# Scraping & parsing data from the job_links
df_job_link = scp.extract_job_links(
    df_search_page=df_search_page,
    load_sleep_time=10,
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
final_df.to_csv('../data/raw/warehouse/07112023-warehouse.csv', index=False)
