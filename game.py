import pandas as pd
import numpy as np
import random
import time
import os
import sqlite3
from threading import Timer
import Components.Items as Items
import Components.Tools as Tools
import time

rock = Items.Item("Rock", "A small rock", 0)
a = rock.__str__()
print(a)

pickaxe = Tools.Tool("Pickaxe", 1, True, "A pickaxe", 1, 10)
b = pickaxe.__str__()
print(b)

    


