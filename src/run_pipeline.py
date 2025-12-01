import os
from utils.scraper import scrape_comments
from src.data_analyzer import run_analysis
from timeit import default_timer as timer

DATA_DIR = "data"
CSV_FILE_PATH = os.path.join(DATA_DIR, "raw_comments.csv")

if __name__ == "__main__":
    """Version 1 of offline pipeline.
    
    1. Scrape all raw data and save to CSV.
    2. Analyze raw data with local ML models: Sentiment and Keywords
    """
    
    print("-- Starting the data pipeline --")
    pipeline_start_time = timer()

    # --- STEP 1: SCRAPE DATA ---
    print("-- Starting data scraping --")
    comments_df = scrape_comments(
        data_dir=DATA_DIR,
        csv_path=CSV_FILE_PATH
    )
    print("Data scraping finished.")
    
    # --- STEP 2: ANALYZE DATA ---
    print("-- Starting data analysis --")
    run_analysis(csv_path=CSV_FILE_PATH)

    pipeline_end_time = timer()
    print(f"\nPipeline finished after  {pipeline_end_time - pipeline_start_time:.2f} seconds..")
    