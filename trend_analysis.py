import sys
import sqlite3
import numpy as np
import pandas as pd
import statsmodels.api as sm

from pathlib import Path
from skmap.misc import date_range, ttprint
from dateutil.relativedelta import relativedelta
from skmap.io.process import SeasConvFill, WhittakerSmooth
from skmap import parallel 
from statsmodels.tsa.seasonal import STL

from loguru import logger

logger.add("trend_log_do_.log", rotation="500 MB")
#field_id = 'ID_POL'

################################
## Analysis functions 
################################

def extract_ts(df,dt_5days):
  """
  Extracts time series data from the DataFrame for 5-day intervals.

  Parameters:
  - df: DataFrame containing the data.
  - dt_5days: List of 5-day intervals.

  Returns:
  - Time series data and corresponding dates.
  """

  ts, dates = [], []

  for dt1, dt2 in dt_5days:

    #try:    

    #df_dt = df.loc[dt1:dt2]

    df_dt = df.loc[(df['date'] >= dt1) & (df['date'] <= dt2)]

    #ts_a.append( df_dt['NDVI_median'].mean() )
    #ts_b.append( df_dt[df_dt['Pixel_used'] > 50]['NDVI_median'].mean() )
    ts.append( df_dt[df_dt['Pixel_used'] >= 70]['NDVI_median'].mean() )
  
    dates.append((dt2 - relativedelta(days=2)).strftime('%Y-%m-%d'))
    #except:
    #  ts.append(np.nan)
    #  dates.append((dt2 - relativedelta(days=2)).strftime('%Y-%m-%d'))
    #  #continue
  
  ts = np.stack([np.stack([ts])])
  return ts, dates

def gapfill(ts, dates,season_size):
  """
  Fills gaps in the time series data.

  Parameters:
  - ts: Time series data.
  - dates: List of dates corresponding to the time series data.
  - season_size: Size of the seasonal period.

  Returns:
  - Filled time series data and updated dates.
  """
  
  seasconv = SeasConvFill(season_size=season_size)
  ts = seasconv._gapfill(ts)
  ### Skipping the days added only match the regular season_size in the gapfilling
  return ts[:,:,10:], dates[10:] 

def sm_trend(ts, season_size, seasonal_smooth):
  """
  Applies seasonal decomposition and trend smoothing to the time series data.

  Parameters:
  - ts: Time series data.
  - season_size: Size of the seasonal period.
  - seasonal_smooth: Size of the seasonal smoothing.

  Returns:
  - Trend analysis results and column names.
  """
  
  sm_cols = ['intercept_m', 'intercept_sd', 'intercept_tv', 'intercept_pv', 'trend_m', 'trend_sd', 'trend_tv', 'trend_pv',
             'r2', 'diff_trend']
  
  result = []
  
  for i in range(0,ts.shape[1]):
    res = STL(ts[0,i,:], period=season_size, seasonal=seasonal_smooth, trend= (2 * season_size) + 1, robust=True).fit()
    y = res.trend
    
    diff_trend = (res.trend[-1] - res.trend[0])

    y_size = y.shape[0]
    X = np.array(range(0, y_size)) / y_size

    X = sm.add_constant(X)
    model = sm.OLS(y,X)
    results = model.fit()

    #print(results.params)

    result_stack = np.stack([
      results.params,
      results.bse,
      results.tvalues,
      results.pvalues
    ],axis=1)

    result.append(np.concatenate([
      result_stack[0,:],
      result_stack[1,:],
      np.stack([results.rsquared, diff_trend])
    ]))
  
  result = np.stack([np.stack(result)])
  return result, sm_cols

def run(input_file, id_pol, dt_5days, season_size,field_id, output_file):
  """
  Executes the trend analysis workflow for a given polygon ID.

  Parameters:
  - input_file: Input database file.
  - id_pol: ID of the polygon.
  - dt_5days: List of 5-day intervals.
  - season_size: Size of the seasonal period.
  - output_file: Output file path.

  Returns:
  - ID of the processed polygon.
  """
  
  #try:  
  con = sqlite3.connect(f'file:{input_file}?mode=ro', uri=True)

  df_sql = f"SELECT *, ((Pixel_Count*1.0 / Total_Pixels) * 100) as Pixel_used FROM restoration WHERE {field_id} = {id_pol}"
  df =  pd.read_sql_query(df_sql, con=con)
  df['date'] = pd.to_datetime(df['date'], errors='coerce')
  #df = df.set_index('date')

  #logger.info(f'Number of objects to process: {total}')
  
  ts, dates = extract_ts(df,dt_5days)

  #print(ts)

  ts, dates = gapfill(ts, dates,season_size)

  trend, trend_cols = sm_trend(ts, season_size, season_size + 2)
  ts_type = np.array([[[int(id_pol), 1]]])
  
  columns = ['id_pol', 'type'] + trend_cols + [ f'd_{d}' for d in dates ]
  
  result = pd.DataFrame(np.concatenate([ts_type, trend, ts], axis=-1)[0,:,:], columns=columns)
  result = result.round(8)
  result['id_pol'] = result['id_pol'].astype(int)
  
  result.to_parquet(output_file,partition_cols=['id_pol'])
  ttprint(f"Polygon {id_pol} saved in {output_file}")
  return id_pol
  #except:
  #  ttprint(f"Polygon {id_pol} FAILED")

# if __name__ == '__main__':

#   # files_list = ['Araticum_ORR','areas_SIR_TNC','Base_PACTO_COALIZAO','BlackJaguar_Areas','EDEN_RESTAURACAO',
#   #   'EMAS_ORR','ICRAF_AREAS','ICV_restauracao','ippara_cf_dg5_restaurooutros','ippara_cf_dg5_restaurosaf',
#   #   'ippara_cf_dg5_safantigo','ippara_cf_dg5_safnovo','main_reflorestar_2021_revisado',
#   #   'mantiqueira_112023_restauracao','MA_PAI_001','MA_PAI_002','mpba_102023_app','mpba_102023_veg',
#   #   'ORR_Imazon','Pratigi_Pai1_ORR','Pratigi_Pai2_ORR','Restauracao_CEVP','Restauracao_Suzano_r_utf8',
#   #   'restauramazonia_saf_v06_10_2023','Sare_Sirgas','UEMARousseau']
  
#   files_list = ['mpba_102023_app']

#   #files_list = ['mpba_102023_app']

#   for file in files_list:

#     input_file = 'DBS/'+file+'.db'
#     field_id = 'ID_POL'
#     start_date, end_date = '2019-01-01', '2024-01-01'
#     output_file = f'{input_file[:-3]}_trend_analysis.pq'

#     ################################
#     ## SQLITE access
#     ################################
#     ttprint(f"Preparing {input_file}")
#     con = sqlite3.connect(input_file)
#     cur = con.cursor()
#     res = cur.execute(f"CREATE INDEX IF NOT EXISTS restoration_id_pol ON restoration ({field_id})")
#     con.commit()
    
#     ################################
#     ## Common data structures
#     ################################
#     ttprint(f"Preparing polygon ids")
    
#     idx_sql = f"SELECT {field_id}, MIN(date) min_date, MAX(date) max_date, COUNT(*) count FROM restoration GROUP BY 1 ORDER BY 1"
#     idx =  pd.read_sql_query(idx_sql, con=con)
    
#     dt_5days = list(date_range(start_date, end_date, date_unit='days', date_step=5, ignore_29feb=True))
#     season_size = int(len(dt_5days) / 5)

#     #run(input_file, idx.iloc[0][f'{field_id}'],dt_5days,season_size,output_file)
#     #run(input_file, 8389,dt_5days,season_size,output_file)

#     args = [ (input_file, r[f'{field_id}'], dt_5days, season_size, output_file) for _, r in idx.iterrows() ]
    
#     ttprint(f"Starting trend analysis on {len(args)} polygons")
#     for id_pol in parallel.job(run, args, joblib_args={'backend': 'multiprocessing'}):
#      continue