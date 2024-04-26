from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
import pandas as pd
from scipy.stats import norm
import numpy as np
import json


def index(request):
    return JsonResponse(
        {
            "Risk aversion parameter in the income function ": "ρ",
            "Risk aversion parameter in the bequest function ": "γ",
            "Risk aversion scaling parameter for bequest": "K2",
            "inflation-free retrun": "ifr",
            "Pension asset test minimum": "AT_min",
            "Pension asset test maximum": "AT_max",
            "Risk aversion additive parameter for income": "K1",
            "consumer price inflation": "Inft",
            "Standard deviation of annual inflation": "σinf",
            "Inflation mean reversion parameter": "α",
            "Equilibrium level of inflation ": "Inf_Eq",
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


def result(request):
    γ = float(request.GET.get("γ"))
    σinf = float(request.GET.get("σinf"))
    α = float(request.GET.get("α"))
    Inf_Eq = float(request.GET.get("Inf_Eq"))
    RWG = float(request.GET.get("RWG"))
    Inft = float(request.GET.get("Inft"))
    Bt = float(request.GET.get("Bt"))
    ρ = float(request.GET.get("ρ"))
    Pt = float(request.GET.get("Pt"))
    K2 = float(request.GET.get("K2"))
    K1 = float(request.GET.get("K1"))
    pen = float(request.GET.get("pen"))
    AT_min = float(request.GET.get("AT_min"))
    AT_max = float(request.GET.get("AT_max"))
    end_age = int(request.GET.get("end_age"))
    start_age = int(request.GET.get("start_age"))
    simulationtimes = int(request.GET.get("simulationtimes"))
    ifr = float(request.GET.get("ifr"))

    life_expectancy_sheet = pd.read_excel("./Life Expectancy.xlsx")

    repeated_data = np.tile(
        life_expectancy_sheet[["Age", "LE_t (years)", "Prob_t"]],
        (simulationtimes, 1),
    )

    sheet = pd.DataFrame(repeated_data, columns=["Age", "LE_t (years)", "Prob_t"])

    sheet["livePossible"] = np.random.rand(
        simulationtimes * (len(life_expectancy_sheet))
    )
    sheet["Z1"] = norm.ppf(
        np.random.rand(simulationtimes * (len(life_expectancy_sheet)))
    )
    sheet["Z2"] = norm.ppf(
        np.random.rand(simulationtimes * (len(life_expectancy_sheet)))
    )

    for i in range(start_age, end_age):
        condition = sheet["Age"] == i
        """
        func7: Inf(t) = ( Inf_Eq + α(Inf(t-1) - Inf_Eq) ) + Z1 * σ(inf)
        """

        if i == start_age:
            sheet.loc[condition, "Inf(t)"] = Inft
        else:
            sheet["Inf(t)"] = sheet["Inf(t)"].fillna(
                Inf_Eq + α * (sheet["Inf(t)"].shift(1) - Inf_Eq) + sheet["Z1"] * σinf
            )
        """
        func6: Pen(t) = Pen(t-1) * (1 + Inf(t-1) + RWG)
        """
        if i == start_age:
            sheet.loc[condition, "Pen(t)"] = None
        if i == start_age + 1:
            sheet.loc[condition, "Pen(t)"] = pen
        else:
            sheet["Pen(t)"] = sheet["Pen(t)"].fillna(
                sheet["Pen(t)"].shift(1) * (1 + sheet["Inf(t)"].shift(1) + RWG)
            )

        """
        func5: r(t) = (inf(t) + RIR + MRP) + Z2 * σ(Port)
        """
        sheet.loc[condition, "r(t)"] = sheet.loc[condition, "Inf(t)"] + ifr

        """
        func4: B(t) = B(t-1) * (1 - 1/(  LE(t-1)  ))*( 1 +  r(t)  )
        """
        if i == start_age:
            sheet.loc[condition, "B(t)"] = Bt
        else:
            sheet.loc[condition, "B(t)"] = sheet.loc[condition, "B(t)"].fillna(
                sheet["B(t)"].shift(1)
                * (1 - 1 / sheet["LE_t (years)"].shift(1))
                * (1 + sheet["r(t)"])
            )

        """
        AT_min(t) = AT_min(t-1) (1 + inf(t-1) + RWG)
        AT_max(t) = AT_max(t-1) (1 + inf(t-1) + RWG)
        """
        if i == start_age:
            sheet.loc[condition, "AT_min"] = AT_min
            sheet.loc[condition, "AT_max"] = AT_max
        else:
            sheet["AT_min"] = sheet["AT_min"].fillna(
                sheet["AT_min"].shift(1) * (1 + sheet["Inf(t)"] + RWG)
            )
            sheet["AT_max"] = sheet["AT_max"].fillna(
                sheet["AT_max"].shift(1) * (1 + sheet["Inf(t)"] + RWG)
            )

        """
        Loss(t)=(B(t)-AT_min) * (Pen(t) / (AT_max-AT_min))
        """
        sheet.loc[condition, "Loss(t)"] = (
            sheet.loc[condition, "B(t)"] - sheet.loc[condition, "AT_min"]
        ) * (
            sheet.loc[condition, "Pen(t)"]
            / (sheet.loc[condition, "AT_max"] - sheet.loc[condition, "AT_min"])
        )

        """
        PR(t) = Max{Min[(Pen(t)-Loss(t)),Pen(t)],0}
        """

        sheet.loc[condition, "PR(t)"] = np.maximum(
            np.minimum(
                sheet.loc[condition, "Pen(t)"] - sheet.loc[condition, "Loss(t)"],
                sheet.loc[condition, "Pen(t)"],
            ),
            0,
        )
        """
        func3: I(t) = B(t-1) / LE(t-1) + PR(t)
        """
        if i > start_age:
            sheet["I(t)"] = sheet["I(t)"].fillna(
                sheet["B(t)"].shift(1) / sheet["LE_t (years)"].shift(1) + sheet["PR(t)"]
            )
        else:
            sheet.loc[condition, "I(t)"] = np.nan

        """
        func2: P(t) = P(t-1) * (1 + Inf(t))
        """
        if i == start_age:
            sheet.loc[condition, "P(t)"] = Pt
        else:
            sheet.loc[condition, "P(t)"] = sheet["P(t)"].fillna(
                sheet["P(t)"].shift(1) * (1 + sheet["Inf(t)"])
            )

        """
        func1: w(t) =  ( I(t) / P(t) )** (1-ρ) / (1 - ρ)  -K1
        """
        if i > start_age:
            sheet.loc[condition, "w"] = (
                (sheet.loc[condition, "I(t)"] / sheet.loc[condition, "P(t)"]) ** (1 - ρ)
            ) / (1 - ρ) - K1
        else:
            sheet.loc[condition, "w"] = 0
            sheet.loc[condition, "W"] = 0

        # check passing
        sheet.loc[condition, "aliveCode"] = np.where(
            sheet.loc[condition, "Prob_t"] > sheet.loc[condition, "livePossible"],
            np.nan,
            1,
        )
        sheet["W"] = sheet["W"].fillna(
            sheet["W"].shift(1) + sheet["w"] * sheet["aliveCode"]
        )

        """
        func8: Y(T) = K2 * ( B(T) / P(T) )**(1 - γ) / (1 - γ)
        """
        sheet.loc[condition, "Y"] = (
            K2
            * (sheet.loc[condition, "B(t)"] / sheet.loc[condition, "P(t)"]) ** (1 - γ)
            / (1 - γ)
        )

        # dead year
    condition = (sheet["W"].notna()) & (sheet["W"].shift(-1).isna())

    final_sheet = sheet[condition]
    final_sheet["W+Y"] = final_sheet["W"] + final_sheet["Y"]
    json_data = final_sheet.to_json(orient="records")

    return JsonResponse(json_data, safe=False)