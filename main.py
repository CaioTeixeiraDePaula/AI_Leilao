from configs import *
from src.scrapper import run_scrap
from src.processor import process_and_save_data


for classification in URLS:
    run_scrap(
        base_url=URLS[classification], 
        card_container_class=CARD_CONTAINER_CLASS,
        summary_class=SUMMARY_CLASS,
        output_file=JSON_FILE,
        time_delay=1.0
    )