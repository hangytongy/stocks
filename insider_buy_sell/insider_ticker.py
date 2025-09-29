#Get insider selling/buying

import pandas as pd
from utils import get_symbols_from_google_sheet, insider_analysis, send_telegram_message
import time 



if __name__ == "__main__":
    tickers = get_symbols_from_google_sheet()
    days = 30

    all_dfs = []

    print(tickers)

    for ticker in tickers:
        print(f"evaluating {ticker}")
        url = f"http://openinsider.com/screener?s={ticker}&o=&pl=&ph=&ll=&lh=&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
        df = insider_analysis(url)
        if df is not None and not df.empty:
            all_dfs.append(df)
            send_telegram_message(f"**{ticker} insider activity the last {days} days** \n\n {df}")
        time.sleep(1)

#    if all_dfs:
#        combined_df = pd.concat(all_dfs, ignore_index=True)
#        msg = combined_df.to_markdown(index=False)
#        send_telegram_message(f"**insider activity the last {days} days** \n\n {msg}")
