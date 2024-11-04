from theropoda import run as theropoda_run
from theropoda import build_id_list
from trend_analysis import run as trend_run
import os
import argparse
import shutil
import sqlite3
import pandas as pd
from skmap.misc import date_range, ttprint
from skmap import parallel

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Toolkit created to extract Time Series information from Sentinel 2 stored in Earth Engine, perform gap filling and trend analysis image.')
    
  parser.add_argument('--asset', type=str, required=True, help='The asset name or path')
  parser.add_argument('--id_field', type=str, required=True, help='The ID field name')
  parser.add_argument('--output_name', type=str, required=True, help='The output file name')

  args = parser.parse_args()

  asset = args.asset #'users/vieiramesquita/LAPIG_FieldSamples/lapig_goias_fieldwork_2022_50m' #Earth Engine Vector Asset
  id_field = args.id_field #'ID_POINTS' #Vector collumn used as ID (use unique identifiers!)
	
  db = asset.split('/')[-1]
  
  #db_name = args.output_name +'.db' #db + '.db'  
  
  colab_folder = ''
  output_name = args.output_name #db_name

  conn = sqlite3.connect(output_name+'.db')
  conn.close()

  #Check if polygon list file exists
  if os.path.exists(os.path.join(colab_folder,db + '_polygonList.txt')) is False:
   build_id_list(asset,id_field,colab_folder,output_name)

  theropoda_run(asset,id_field,output_name,colab_folder,db)
  
  start_date_trend, end_date_trend= '1997-01-01', '2008-01-01'
  output_file_trends = f'{output_name}_trend_analysis.pq'

  ################################
  ## SQLITE access
  ################################
  ttprint(f"Preparing {output_name}")
  con = sqlite3.connect(output_name+'.db')
  cur = con.cursor()
  res = cur.execute(f"CREATE INDEX IF NOT EXISTS restoration_id_pol ON restoration ({id_field})")
  con.commit()
  
  ################################
  ## Common data structures
  ################################
  ttprint(f"Preparing polygon ids")
  
  idx_sql = f"SELECT {id_field}, MIN(date) min_date, MAX(date) max_date, COUNT(*) count FROM restoration GROUP BY 1 ORDER BY 1"
  idx =  pd.read_sql_query(idx_sql, con=con)
  
  dt_5days = list(date_range(start_date_trend, end_date_trend, date_unit='days', date_step=16, ignore_29feb=True))
  season_size = int(len(dt_5days) / 16)

  args = [ (output_name+'.db', r[f'{id_field}'], dt_5days, season_size, id_field, output_file_trends) for _, r in idx.iterrows() ]
  
  ttprint(f"Starting trend analysis on {len(args)} polygons")
  for id_pol in parallel.job(trend_run, args, joblib_args={'backend': 'multiprocessing'}):
    continue
  
  df2conv = pd.read_parquet(output_file_trends)
  df2conv.to_parquet(f'{output_name}_trend_analysis.parquet')

  shutil.rmtree(output_file_trends)  
