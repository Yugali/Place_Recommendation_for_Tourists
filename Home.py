from builtins import print

from flask import Flask, request, render_template, redirect, url_for, logging, json, session, jsonify, flash
from flaskext.mysql import MySQL
import csv
import pandas as pd
import numpy as np

def recommendCity(userid):
    Ratings = pd.read_csv("Ratings.csv", encoding="ISO-8859-1")

    Mean = Ratings.groupby(['userId'], as_index=False, sort=False).mean().rename(columns={'rating': 'rating_mean'})[
        ['userId', 'rating_mean']]
    Ratings = pd.merge(Ratings, Mean, on='userId', how='left', sort=False)
    Ratings['rating_adjusted'] = Ratings['rating'] - Ratings['rating_mean']

    distinct_users = np.unique(Ratings['userId'])

    user_data_append = pd.DataFrame()

    user_data_all = pd.DataFrame()

    user1_data = Ratings[Ratings['userId'] == userid]
    user1_mean = user1_data["rating"].mean()
    user1_data = user1_data.rename(columns={'rating_adjusted': 'rating_adjusted1'})
    user1_data = user1_data.rename(columns={'userId': 'userId1'})
    user1_val = np.sqrt(np.sum(np.square(user1_data['rating_adjusted1']), axis=0))

    distinct_place = np.unique(Ratings['cityId'])
    i = 1
    print(distinct_place[9:10])
    for place in distinct_place:
        item_user = Ratings[Ratings['cityId'] == place]

        distinct_users1 = np.unique(item_user['userId'])

        j = 1

        for user2 in distinct_users1:

            if j % 200 == 0:
                print(j, "out of ", len(distinct_users1), i, "out of ", len(distinct_place))

            user2_data = Ratings[Ratings['userId'] == user2]
            user2_data = user2_data.rename(columns={'rating_adjusted': 'rating_adjusted2'})
            user2_data = user2_data.rename(columns={'userId': 'userId2'})
            user2_val = np.sqrt(np.sum(np.square(user2_data['rating_adjusted2']), axis=0))

            user_data = pd.merge(user1_data, user2_data[['rating_adjusted2', 'cityId', 'userId2']], on='cityId',
                                 how='inner', sort=False)
            user_data['vector_product'] = (user_data['rating_adjusted1'] * user_data['rating_adjusted2'])

            user_data = user_data.groupby(['userId1', 'userId2'], as_index=False, sort=False).sum()

            user_data['dot'] = user_data['vector_product'] / (user1_val * user2_val)

            user_data_all = user_data_all.append(user_data, ignore_index=True)

            j = j + 1

        user_data_all = user_data_all[user_data_all['dot'] < 1]
        user_data_all = user_data_all.sort_values(['dot'], ascending=False)
        user_data_all = user_data_all.head(30)
        user_data_all['cityId'] = place
        user_data_append = user_data_append.append(user_data_all, ignore_index=True)
        i = i + 1

        User_dot_adj_rating_all = pd.DataFrame()

        distinct_places = np.unique(Ratings['cityId'])

        j = 1
        for place in distinct_places:
            user_data_append_place = user_data_append[user_data_append['cityId'] == place]
            User_dot_adj_rating = pd.merge(Ratings, user_data_append_place[['dot', 'userId2', 'userId1']], how='inner',
                                           left_on='userId', right_on='userId2', sort=False)

            if j % 200 == 0:
                print(j, "out of ", len(distinct_places))

            User_dot_adj_rating1 = User_dot_adj_rating[User_dot_adj_rating['cityId'] == place]

            if len(np.unique(User_dot_adj_rating1['userId'])) >= 2:
                User_dot_adj_rating1['wt_rating'] = User_dot_adj_rating1['dot'] * User_dot_adj_rating1[
                    'rating_adjusted']

                User_dot_adj_rating1['dot_abs'] = User_dot_adj_rating1['dot'].abs()
                User_dot_adj_rating1 = User_dot_adj_rating1.groupby(['userId1'], as_index=False, sort=False).sum()[
                    ['userId1', 'wt_rating', 'dot_abs']]
                User_dot_adj_rating1['Rating'] = (User_dot_adj_rating1['wt_rating'] / User_dot_adj_rating1[
                    'dot_abs']) + user1_mean
                User_dot_adj_rating1['cityId'] = place
                User_dot_adj_rating1 = User_dot_adj_rating1.drop(['wt_rating', 'dot_abs'], axis=1)

                User_dot_adj_rating_all = User_dot_adj_rating_all.append(User_dot_adj_rating1, ignore_index=True)

            j = j + 1

        User_dot_adj_rating_all = User_dot_adj_rating_all.sort_values(['Rating'], ascending=False)
        print(User_dot_adj_rating_all)

    return(User_dot_adj_rating_all)

mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER']='root'
app.config['MYSQL_DATABASE_PASSWORD']='root'
app.config['MYSQL_DATABASE_DB']='test'
app.config['MYSQL_DATABASE_POST']='localhost'
mysql.init_app(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route("/")
def gotohome():
    return render_template('Home.html')

@app.route("/home")
def my_form():
    flash("")
    return render_template('Home.html')

@app.route('/register', methods=['POST'])
def register():
    return render_template('Register.html')

@app.route('/registerUser', methods=['POST'])
def registerUser():
    username = str(request.form['username'])
    email = str(request.form['email'])
    password = str(request.form['password'])
    con = mysql.connect()
    cursor = con.cursor()
    data = cursor.execute("INSERT INTO users (username, email, password) VALUES(%s, %s, %s)",(username, email, password))
    con.commit()

    if data == 1:
        flash("")
        return render_template('Home.html')
    else:
        return "Not Inserted"

@app.route('/login', methods=['POST'])
def login():
    username = str(request.form['username'])
    password = str(request.form['password'])
    con = mysql.connect()
    cursor = con.cursor()
    cursor.execute("SELECT id from users where username= '" + username + "' and password= '" + password + "' ")
    data = cursor.fetchone()
    if data is None:
        flash("Username/Password is incorrect")
        return render_template('Home.html')
    else:
        cursor.execute("SELECT city.name,ratings.rating from ratings INNER JOIN city ON ratings.cityid = city.id and userid= '" + str(data[0]) + "'")
        allData = cursor.fetchall()
        session['allData'] = allData
        session['length'] = len(allData)
        session['userId'] = data
        session['recommendFlag'] = 0;
        return redirect(url_for("profile",name = data))


@app.route('/profile')
def profile():
    session['recommendFlag'] = 0;
    return render_template('Profile.html')

@app.route('/rating', methods=['POST'])
def rating():
    for cityname, rating in zip(request.form.getlist('cityname'),request.form.getlist('rating')):
        con = mysql.connect()
        cursor = con.cursor()
        data = cursor.execute("INSERT INTO ratings (userid, cityid, rating) VALUES(%s, %s, %s)",(int(request.form['username']), int(cityname), int(rating)))
        con.commit()
    return render_template('Home.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    con = mysql.connect()
    cursor = con.cursor()
    query = 'SELECT * FROM ratings;'
    cursor.execute(query)
    result = cursor.fetchall()
    userid = session['userId']
    with open("Ratings.csv", "w",newline='') as myfile:
        c = csv.writer(myfile, delimiter=',', quotechar='"')
        c.writerow(["userId", "cityId", "rating"])
        for row in result:
            c.writerow(row)

    cityid = recommendCity(userid[0])
    print("returned")

    query = "SELECT cityid FROM ratings where userid = '" + str(userid[0]) + "' ORDER BY rating DESC;"
    cursor.execute(query)
    cityData = cursor.fetchall()
    flag = 0
    for index, row in cityid.iterrows():
        for i in cityData:
            if(int(row['cityId']) == int(i[0])):
                flag = 0
                break
            else:
                flag = 1
        if flag == 1:
            break


    print(row['cityId'])
    query = "SELECT name FROM city where id= '" + str(row['cityId']) + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    session['recommendFlag'] = 1
    session['recommendCity'] = result[0]
    return render_template('Profile.html')

if __name__ == '__main__':
    app.run()

