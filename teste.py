from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium.webdriver.common.keys import Keys
import csv
import datetime
import os
import pytz
import smtplib
import email.message
import psutil
import re
import numpy as np

new = pd.read_csv("new.csv")
old = pd.read_csv("old.csv")

comparar = pd.merge(
    new, 
    old, 
    on = 'CAAE', 
    how = 'outer',
    suffixes=('_new', '_old')
    )
comparar = comparar[comparar["new"] != comparar["old"]]