import pandas as pd
import numpy as np

Ratings=pd.read_csv("Ratings.csv",encoding="ISO-8859-1")

Ratings_mean=Ratings.groupby(['cityId'])[['rating']].mean().rename(columns = {'rating': 'Mean_rating'}).reset_index()

# Calculating damped mean using alpha = 5

Ratings_sum=Ratings.groupby(['cityId'])[['rating']].sum().rename(columns = {'rating': 'sum_rating'}).reset_index()
Ratings_sum['sum_rating_factor']=Ratings_sum['sum_rating']+5*(Ratings["rating"].mean())

Ratings_count=Ratings.groupby(['cityId'])[['rating']].count().rename(columns = {'rating': 'count_rating'}).reset_index()
Ratings_count['count_rating_factor']=Ratings_count['count_rating']+5

Ratings_damped=pd.merge(Ratings_sum,Ratings_count[['cityId','count_rating','count_rating_factor']],on=['cityId'],how='left')
Ratings_damped['damped_mean']=Ratings_damped['sum_rating_factor']/Ratings_damped['count_rating_factor']
Ratings_mean_dampmean=pd.merge(Ratings_mean[['cityId','Mean_rating']],Ratings_damped[['cityId','damped_mean']],on=['cityId'],how='left')

# Sorting to get top rated movies

Ratings_mean_dampmean = Ratings_mean_dampmean.sort_values(['Mean_rating'], ascending=False)

print(Ratings_mean_dampmean)