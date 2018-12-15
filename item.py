import pandas as pd
import numpy as np
import math

Ratings=pd.read_csv("Ratings.csv",encoding="ISO-8859-1")

Mean= Ratings.groupby(['cityId'], as_index = False, sort = False).mean().rename(columns = {'rating': 'rating_mean'})[['cityId','rating_mean']]
Ratings = pd.merge(Ratings,Mean,on = 'cityId', how = 'left', sort = False)
Ratings['rating_adjusted']=Ratings['rating']-Ratings['rating_mean']

place_data_all_append = pd.DataFrame()

user_data = Ratings[Ratings['userId'] != 51]
distinct_places = np.unique(user_data['cityId'])
i = 1
for place in distinct_places:

    if i % 10 == 0:
        print(i, "out of ", len(distinct_places))

    place_data_all = pd.DataFrame()

    place_data = Ratings[Ratings['cityId'] == place]
    place_data = place_data[['userId', 'cityId', 'rating_adjusted']].drop_duplicates()
    place_data = place_data.rename(columns={'rating_adjusted': 'rating_adjusted1'})
    place_data = place_data.rename(columns={'cityId': 'cityId1'})
    place1_val = np.sqrt(np.sum(np.square(place_data['rating_adjusted1']), axis=0))

    user_data1 = Ratings[Ratings['userId'] == 51]
    distinct_places1 = np.unique(user_data1['cityId'])

    for place1 in distinct_places1:
        place_data1 = Ratings[Ratings['cityId'] == place1]
        place_data1 = place_data1[['userId', 'cityId', 'rating_adjusted']].drop_duplicates()
        place_data1 = place_data1.rename(columns={'rating_adjusted': 'rating_adjusted2'})
        place_data1 = place_data1.rename(columns={'cityId': 'cityId2'})
        place2_val = np.sqrt(np.sum(np.square(place_data1['rating_adjusted2']), axis=0))

        place_data_merge = pd.merge(place_data, place_data1[['userId', 'cityId2', 'rating_adjusted2']], on='userId',
                                    how='inner', sort=False)

        place_data_merge['vector_product'] = (
                    place_data_merge['rating_adjusted1'] * place_data_merge['rating_adjusted2'])

        place_data_merge = place_data_merge.groupby(['cityId1', 'cityId2'], as_index=False, sort=False).sum()

        place_data_merge['dot'] = place_data_merge['vector_product'] / (place1_val * place2_val)

        place_data_all = place_data_all.append(place_data_merge, ignore_index=True)

    place_data_all = place_data_all[place_data_all['dot'] < 1]
    place_data_all = place_data_all.sort_values(['dot'], ascending=False)
    place_data_all = place_data_all.head(20)

    place_data_all_append = place_data_all_append.append(place_data_all, ignore_index=True)
    i = i + 1

    place_rating_all = pd.DataFrame()

    for place in distinct_places:
        place_nbr = place_data_all_append[place_data_all_append['cityId1'] == place]
        place_mean = Ratings[Ratings['cityId'] == place]
        mean = place_mean["rating"].mean()
        place_nbr_dot = pd.merge(user_data1, place_nbr[['dot', 'cityId2', 'cityId1']], how='inner', left_on='cityId',
                                 right_on='cityId2', sort=False)
        place_nbr_dot['wt_rating'] = place_nbr_dot['dot'] * place_nbr_dot['rating_adjusted']
        place_nbr_dot['dot_abs'] = place_nbr_dot['dot'].abs()
        place_nbr_dot = place_nbr_dot.groupby(['cityId1'], as_index=False, sort=False).sum()[
            ['cityId1', 'wt_rating', 'dot_abs']]
        place_nbr_dot['Rating'] = (place_nbr_dot['wt_rating'] / place_nbr_dot['dot_abs']) + mean

        place_rating_all = place_rating_all.append(place_nbr_dot, ignore_index=True)

    place_rating_all = place_rating_all.sort_values(['Rating'], ascending=False)
print(place_rating_all)