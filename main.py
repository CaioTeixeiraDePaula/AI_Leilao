from configs import *
from modules import *


for classification in URLS:
    run_scrap(
        base_url=URLS[classification], 
        card_container_class=CARD_CONTAINER_CLASS,
        summary_class=SUMMARY_CLASS,
        output_file=JSON_FILE,
        time_delay=0.15
    )

    process_and_save_data(
        input_json_file=JSON_FILE,
        db_name=DB_NAME,
        score_threshold=7    
    )