from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
import pandas as pd
import random
from scipy.stats import norm


def index(request):
    return JsonResponse(
        {
            "Risk aversion parameter in the income function ": "ρ",
            "Risk aversion parameter in the bequest function ": "γ",
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

def default(request):
    return JsonResponse(
        {
            "γ": 0.4,
            "σinf": 0.03,
            "α": 0.6,
            "Inf_Eq": 0.025,
            "RWG": 0.01,
            "σport": 0.15,
            "MRP": 0.01,
            "RIR": 0.01,
            "Inft": 0.025,
            "Bt": 300000,
            "ρ": 0.7,
            "Pt": 1000,
            "pen": 29000,
        }
    )


def result(request):
    γ = float(request.GET.get("γ"))
    σinf = float(request.GET.get("σinf"))
    α = float(request.GET.get("α"))
    Inf_Eq = float(request.GET.get("Inf_Eq"))
    RWG = float(request.GET.get("RWG"))
    σport = float(request.GET.get("σport"))
    MRP = float(request.GET.get("MRP"))
    RIR = float(request.GET.get("RIR"))
    Inft = float(request.GET.get("Inft"))
    Bt = float(request.GET.get("Bt"))
    ρ = float(request.GET.get("ρ"))
    Pt = float(request.GET.get("Pt"))
    pen = float(request.GET.get("pen"))

    life_expectancy_sheet = pd.read_excel("./Life Expectancy.xlsx")

    sheet_simulation = pd.DataFrame(columns=life_expectancy_sheet.columns.tolist())
    W = 0
    # start one simulation
    for t in range(len(life_expectancy_sheet)):
        sheet_simulation.loc[t] = life_expectancy_sheet.loc[t]

        """
        func7: Inf(t) = ( Inf_Eq + α(Inf(t-1) - Inf_Eq) ) + Z * σ(inf)
        """
        α = sheet_simulation.loc[t, "α"] = α
        σ = sheet_simulation.loc[t, "σ(inf)"] = σinf
        Inf_Eq = sheet_simulation.loc[t, "Inf_Eq"] = Inf_Eq

        Z = sheet_simulation.loc[t, "Z1"] = norm.ppf(random.random())

        if t == 0:
            inf = sheet_simulation.loc[t, "inf"] = Inft
        else:
            inf = sheet_simulation.loc[t, "inf"] = (
                Inf_Eq + α * (sheet_simulation.loc[t - 1, "inf"] - Inf_Eq)
            ) + Z * σ

        """
        func6: Pen(t) = Pen(t-1) * (1 + Inf(t-1) + RWG)
        """
        RWG = sheet_simulation.loc[t, "RWG"] = RWG

        if t > 1:
            pen = sheet_simulation.loc[t, "Pen"] = sheet_simulation.loc[
                t - 1, "Pen"
            ] * (1 + sheet_simulation.loc[t - 1, "inf"] + RWG)
        elif t == 1:
            pen = sheet_simulation.loc[t, "Pen"] = pen
        else:
            pass

        """
        func5: r(t) = (inf(t) + RIR + MRP) + Z * σ(Port)
        """
        RIR = sheet_simulation.loc[t, "RIR"] = RIR
        MRP = sheet_simulation.loc[t, "MRP"] = MRP
        Z = sheet_simulation.loc[t, "Z2"] = norm.ppf(random.random())
        σPort = sheet_simulation.loc[t, "σ(Port)"] = σport

        rt = sheet_simulation.loc[t, "r(t)"] = (inf + RIR + MRP) + Z * σPort

        """
        func4: B(t) = B(t-1) * (1 - 1/(  LE(t-1)  ))*( 1 +  r(t)  )
        """
        if t == 0:
            B = sheet_simulation.loc[t, "B"] = Bt
        else:
            B = sheet_simulation.loc[t, "B"] = (
                sheet_simulation.loc[t - 1, "B"]
                * (1 - 1 / sheet_simulation.loc[t - 1, "LE_t (years)"])
                * (1 + rt)
            )

        """
        func3: I(t) = B(t-1) / LE(t-1) + Pen(t)
        """
        if t > 0:
            I = sheet_simulation.loc[t, "I(t)"] = (
                sheet_simulation.loc[t - 1, "B"]
                / sheet_simulation.loc[t - 1, "LE_t (years)"]
                + pen
            )

        """
        func2: P(t) = P(t-1) * (1 + Inf(t))
        """
        if t == 0:
            sheet_simulation.loc[t, "P"] = Pt
        else:
            P = sheet_simulation.loc[t, "P"] = sheet_simulation.loc[t - 1, "P"] * (
                1 + inf
            )

        """
        func1: w(t) =  ( I(t) / P(t) )** (1-ρ) / (1 - ρ) 
        """
        ρ = sheet_simulation.loc[t, "ρ"] = ρ

        if t > 0:
            w = sheet_simulation.loc[t, "w"] = (I / P) ** (1 - ρ) / (1 - ρ)

        # check passing
        if t > 0:
            W += w
            sheet_simulation.loc[t, "W"] = W
            if random.random() < life_expectancy_sheet.loc[t, "Prob_t"]:
                # passing
                """
                func8: Y(T) = ( B(T) / P(T) )**(1 - γ) / (1 - γ)
                """
                γ = sheet_simulation.loc[t, "γ"] = γ

                Y = sheet_simulation.loc[t, "Y"] = (B / P) ** (1 - γ) / (
                    1 - γ
                )  # Bequest well-being in year T
                W += Y

                sheet_simulation.loc[t, "W"] = W
                break

    sheet_simulation["I(t)/P"] = sheet_simulation["I(t)"] / sheet_simulation["P"]
    sheet_simulation["B/P"] = sheet_simulation["B"] / sheet_simulation["P"]

    json_data = sheet_simulation.to_json(orient="records")

    return JsonResponse(json_data, safe=False)
