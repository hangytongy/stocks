#Get insider selling/buying

import pandas as pd
import time
from utils import insider_analysis, send_telegram_message


days = 7
selling_amount = 100000
buying_amount = 50000
insider_selling = f"http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xs=1&vl={selling_amount}&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
insider_buying = f"http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl={buying_amount}&vh=&ocl=&och=&sic1=-1&sicl=&sich=&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"



if __name__ == "__main__":
    df_sell = insider_analysis(insider_selling)
    if df_sell is not None and not df_sell.empty:
        send_telegram_message(f"***PAST {days} selling activity*** \n\n {df_sell}")
    time.sleep(5)
    df_buy = insider_analysis(insider_buying)
    if df_buy is not None and not df_buy.empty:
        send_telegram_message(f"***PAST {days} buying activity*** \n\n {df_buy}")