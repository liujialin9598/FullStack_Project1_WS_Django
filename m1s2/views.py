from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
import pandas as pd
from scipy.stats import norm
import numpy as np
import json
import ast


def index(request):
    return JsonResponse(
        {
            
            "simulation times": "simulationtimes",
            "Inflation weight": "Z_group",
            "return related Inflation weight": "γ_group",
            "Inflation mean reversion parameter (Inf(t) > Inf_Eq)": "α1",
            "Inflation mean reversion parameter (Inf(t) < Inf_Eq)": "α2",
            "Standard deviation of annual inflation": "σinf",
            "Equilibrium level of inflation ": "Inf_Eq",
            "Risk aversion parameter in the income function": "ρ",
            "Risk aversion parameter in the bequest function ": "γ",
            "Risk aversion scaling parameter for bequest": "K2",
            "Pension asset test minimum": "AT_min",
            "Pension asset test maximum": "AT_max",
            "Risk aversion additive parameter for income": "K1",
            "Real Wage Growth": "RWG",
            "Standard deviation of annual return on members balance": "σport",
            "Market Risk Premium": "MRP",
            "real interest rate": "RIR",
            "Member's balance": "Bt",
            "Price index": "Pt",
            "annual pension payment": "pen",
        }
    )


def compare_and_update_json(new_data, file_path):
    # 读取之前的JSON文件中的数据
    with open(file_path, "r", encoding="utf-8") as file:
        old_data = json.load(file)

    # 比较新的JSON数据与之前的数据，找出差异，并更新之前的JSON数据
    for key, value in new_data.items():
        if key in old_data and old_data[key] != value:
            old_data[key] = value

    # 将更新后的JSON数据写入文件中
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(old_data, file, indent=4)


def default(request):
    with open("./jsonDefault.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    if len(request.GET) > 0:
        compare_and_update_json(request.GET.dict(), "./jsonDefault.json")
    return JsonResponse(data)

