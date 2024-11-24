"""
    Heavily based on: https://saturncloud.io/blog/python-how-to-display-matplotlib-in-flask/
"""

import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from time import time
import time
from elasticsearch import Elasticsearch
import pandas as pd
from hampel import hampel
import math
from math import ceil
import datetime
from datetime import datetime
import sys
import os
from os import environ
from flask import Flask, render_template, request
from flask import render_template_string, redirect
app = Flask(__name__)

def retrieve_points_of_interest(window, std, days, series, testtool):
    es = Elasticsearch([{'host' : os.environ['ELASTIC_USER'], 'port' : 443, "scheme" : "https"}], basic_auth = ('elastic', os.environ['ELASTIC_AUTH']))

    # Since when to retrieve values
    since = int(round(time.time() * 1000)) - int(days) * 86400000 

    # Search for the data
    res = es.search(index = "wifimon", body = {
        "size" : 10000,
        "sort" : { "Timestamp" : "asc" },
        "query" : {
            "range" : {
                "Timestamp" : {
                    "gte" : since
                }
            }
        }
    })

    monitoredValues = []
    timestamps = []

    # Keep values of interest
    for hit in res['hits']['hits']:
        value = hit["_source"][str(series)]
        value = math.ceil(value)
        if hit["_source"]["Test-Tool"] == str(testtool):
            monitoredValues.append(value)
            valueTimestamps = hit["_source"]["Timestamp"]
            timestamps.append(valueTimestamps)

    dfValues = pd.Series( (v for v in monitoredValues) )
    dfTimestamps = pd.Series( (v for v in timestamps) )

    # Anomaly detection based on the Hampel method
    analysis = hampel(dfValues, window_size = int(window), n_sigma = float(std))

    for index in analysis.outlier_indices:
        ts = int(dfTimestamps[index]) / 1000

    return dfValues, analysis.outlier_indices

def create_plot(values, anomaly_points):
    x = np.linspace(0, len(values), num = len(values))
    y = values.to_numpy()

    # Create plots (first plot is the time series, second plot includes the points of interest)
    plt.figure(figsize = (16, 8))
    plt.plot(x, y, "b")
    plt.plot(x, y, "r", markevery = anomaly_points, ls = "", marker = "o", label = "points")
    plt.title('WiFiMon Time Series')
    plt.xlabel('Time')
    plt.ylabel('Monitored Metric')
    plt.grid(True)
    return None

def plot_to_img(window, std, days, series, testtool):
    # Analyze and detect anomalies
    values, anomaly_points = retrieve_points_of_interest(window, std, days, series, testtool)
    # Create plot
    create_plot(values, anomaly_points)

    # Save plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Convert BytesIO object to base64 string
    img_b64 = base64.b64encode(img.getvalue()).decode()

    return img_b64

@app.route("/")
def my_form():
    return render_template("index.html")

@app.route('/', methods = ["POST"])
def plot():
    # Authenticate based on a simple token. If the token does not match, terminate
    if request.form["token"] != os.environ['ANALYSIS_SECRET']:
        return None

    # Retrieve the variable values from the HTML form
    window = request.form["window"]
    std = request.form["std"]
    days = request.form["days"]
    series = request.form["series"]
    testtool = request.form["testtool"]

    # Convert plot to image
    img_b64 = plot_to_img(window, std, days, series, testtool)

    # Render HTML with base64 image
    html = f'<img src="data:image/png;base64,{img_b64}" class="blog-image" width = "auto" height = "auto" alt = "WiFiMon Analysis for Alerts">'
    return render_template_string(html)

if __name__ == '__main__':
    app.run(port = 8888)
