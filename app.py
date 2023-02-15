"""
Script to plot Sentimental analysis data on Reddit data for bitcoin between two dates using already saved data
from CosmosDB. Only works if the data is already saved in the CosmosDB. Doesnt do a live query of
Reddit data.
"""
# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
# import seaborn as sns
# import os
import CosmosDB
from datetime import date, timedelta, datetime
from flask import Flask, request, render_template
from flask_socketio import SocketIO
import json
import plotly
import plotly.express as px


# Method to plot based on the Past days(Default is 7) or based on a date range.
# def plot_db(df_db, start_date=None, end_date=None):
#     # df_db_mon = df_db.loc[start_date:end_date]
#     # df_db_mon = df_db.loc[pd.Timestamp(start_date):pd.Timestamp(end_date)]
#     df_db_mon = df_db.loc[str(start_date):str(end_date)]
#     plt.close()
#     sns.relplot(data=df_db_mon, kind='line', markers=True)
#     plt.xlabel("Date")
#     plt.ylabel("Number of comments")
#     plt.title("Sentiment Trend during " + str(start_date) + " : " + str(end_date))
#     plt.xticks(rotation=60)
#     plt.show()

app = Flask(__name__, template_folder='templates')

# Decorator for html form data
@app.route('/', methods=["GET", "POST"])
def gfg():
    msg = ''
    if request.method == "POST":
        # getting input with name = fname in HTML form
        global topic
        topic = request.form.get("formtopic")
        # getting input with name = lname in HTML form
        start_date = request.form.get("startdt")
        end_date = request.form.get("enddt")

        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        print("Getting Data for Topic: {}, between dates: {} and {}".format(topic, start_date, end_date))

        # Check if a database file/table is present for the current topic
        df_topic = CosmosDB.get_db_items('comments_tab', topic)
        if len(df_topic) > 0:
            # df_topic.index = pd.to_datetime(df_topic.index)
            df_topic = df_topic.sort_index()
            print("df_topic is \n {} ".format(df_topic.head()))
        else:
            msg = "Unable to find the data for bitcoin in the database. Please try again later."
            #df_topic = pd.DataFrame(columns=['Pos', 'Neg'], index=pd.to_datetime([]))

        processed_stats = df_topic.loc[str(start_date):str(end_date)]
        print("processed stats is \n {} ".format(processed_stats.head()))
        # Plot the Data from cumulative stats for a day at a time
        fig = px.line(processed_stats, x=processed_stats.index,
                      y=['Pos', 'Neg'], markers=True).update_layout(title=topic, xaxis_title="Date",
                                                                    yaxis_title="Number of comments")
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('sentDashboard.html', graphJSON=graphJSON, startdt=start_date, enddt=end_date)
    return render_template("form.html")


if __name__ == '__main__':
    start_date = end_date = None
    global topic
    topic = "bitcoin"
    app.run(host='0.0.0.0', debug=False)
    #socketio = SocketIO(app)
    #socketio.run(app, host='0.0.0.0', debug=False, allow_unsafe_werkzeug=True)
