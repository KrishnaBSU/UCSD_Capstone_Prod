"""
Script to generate Sentimental analysis data using Reddit/Pusshift API for Bitcoin daily and then
save the data in the CosmosDB data base.
"""

import pandas as pd
from reddit_data_collection import get_clean_data
import CosmosDB
from datetime import date, timedelta, datetime
import tensorflow as tf
from transformers import BertTokenizer
# import os
# import matplotlib.pyplot as plt
# import numpy as np
# import seaborn as sns


# model = TFBertForSequenceClassification.from_pretrained("bert-base-uncased")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# load a saved model
# Model location in Google Colab
model = tf.keras.models.load_model('./IMDB_BERT_Model256/Model')
# model = tf.keras.models.load_model("C:\\Users\\krish\\OneDrive\\Desktop\\UCSD_ML\\Capstone"
#                                  "\\Scripts\\IMDB_BERT_Model256\\Model")


# Method to predict sentiment from a give data frame
def predict_sent(df):
    # Making Predictions
    pred_sentences = df['comments'].values.tolist()

    # Tokenizing the test sentences
    tf_batch = tokenizer(pred_sentences, max_length=256, padding=True, truncation=True, return_tensors='tf')
    tf_outputs = model(tf_batch)
    # tf_predictions = tf.nn.softmax(tf_outputs[0], axis=-1)
    tf_predictions = tf.nn.softmax(tf_outputs['logits'], axis=-1)
    # labels = ['Negative', 'Positive']
    label = tf.argmax(tf_predictions, axis=1)
    label = label.numpy()
    return list(label)

def get_stats(df, df_comments, start_date, end_date):
    print("Writing in Data base for {} between dates {}  and {}".format(topic, start_date, end_date))
    df_comments = pd.DataFrame()
    day = start_date
    while day < end_date:
        # If the data frame already has the data for the current day, then skip predicting it.
        if str(day) in df.index:
            print("{} already present in the database".format(str(day)))
            day = day + timedelta(1)
            continue
        else:
            df_data = get_clean_data(topic, str(day), str(day+timedelta(1)))
            # Predicting only when there are any comments made.
            if len(df_data) > 0:
                predict_list = predict_sent(df_data)
                pos_count = predict_list.count(1)
                neg_count = predict_list.count(0)
                # Adding the comments and the Predicted values to the data frame along with the date of the comments.
                day_list = [day for i in range(len(df_data))]
                df_temp = pd.DataFrame(list(zip(df_data['comments'].values.tolist(), predict_list)),
                                       columns=['comments', 'sentiment'], index=day_list)
                df_temp.index = pd.to_datetime(df_temp.index)
                df_comments = pd.concat([df_comments, df_temp])
            else:
                pos_count = 0
                neg_count = 0

            # Write the pos and neg count to the data frame base along with the date.
            # df.loc[day] = [pos_count, neg_count]
            df.loc[pd.Timestamp(day)] = [pos_count, neg_count]
            print("Day: {}, +ve count: {}, -ve count: {}".format(day, pos_count, neg_count))
            # Updating the data frame to be written to the db with the rows that only needs to be added.
            global df_to_db
            df_to_db.loc[pd.Timestamp(day)] = [pos_count, neg_count]
            day = day + timedelta(1)
            # Setting flag to write to DB to 1 as we are predicting below.
            global write_to_db
            write_to_db = 1
    # print("DF while writing to DB")
    df.index = pd.to_datetime(df.index)
    # print(df.head(5))
    return [df, df_comments]


if __name__ == '__main__':

    #Flag to write to db only when the data is already not present in the db.
    global write_to_db
    write_to_db = 0
    # Data frame to be exclusively used to store data that needs to be finally written to the the database.
    global df_to_db
    df_to_db = pd.DataFrame({'Pos':[],'Neg':[]},index=pd.to_datetime([]))

    topic = 'bitcoin'

    end_date = date.today()
    start_date = end_date - timedelta(1)
    #end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    #start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    # Check if a database file/table is present for the current topic
    df_topic = CosmosDB.get_db_items('comments_tab', topic)
    if len(df_topic) > 0:
        df_topic = df_topic.sort_index()
    else:
        df_topic = pd.DataFrame(columns=['Pos', 'Neg'], index=pd.to_datetime([]))

    # # Check if a database file/table is present for the current topic with corresponding date, comments and sentiment.
    # dbname_comments = topic + '_comments.pkl'
    # if os.path.isfile(dbname_comments):
    #     df_topic_comments = pd.read_pickle(dbname_comments)
    # else:
    #     df_topic_comments = pd.DataFrame(index=pd.to_datetime([]))

    # Update the dataframes(df_topic -> consolidated by day, df_topic_comments -> each comment with the prediction)
    # with the Positive, Negative counts.
    df_topic_comments = pd.DataFrame()
    processed_stats = get_stats(df_topic, df_topic_comments, start_date, end_date)
    # Plot the Data from cumulative stats for a day at a time
    #plot_db(processed_stats[0], start_date, end_date)
    # Save the Data Frame to Pickle/DB.
    if write_to_db:
        print("Updating DB with Cumulative Predicted stats for each day ")
        CosmosDB.insert_items("comments_tab", df_to_db, topic)
        print("Updating DB with Predicted sentiment for each comment ")
        CosmosDB.insert_items("comments_details_tab", processed_stats[1], topic)
