import json
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


def default(request):
    
    with open("./jsonDefault.json", "r",encoding='utf-8') as file:
        data = json.load(file)
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
    ifr = float(request.GET.get("ifr"))

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
        func5: r(t) = inf(t) +0.01
        """
        rt = sheet_simulation.loc[t, "r(t)"] = inf + ifr

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
        AT_min(t) = AT_min(t-1) (1 + inf(t-1) + RWG)
        AT_max(t) = AT_max(t-1) (1 + inf(t-1) + RWG)
        """
        if t == 0:
            AT_min = sheet_simulation.loc[t, "AT_min"] = AT_min
            AT_max = sheet_simulation.loc[t, "AT_max"] = AT_max
        else:
            AT_min = sheet_simulation.loc[t, "AT_min"] = AT_min * (1 + inf + RWG)
            AT_max = sheet_simulation.loc[t, "AT_max"] = AT_max * (1 + inf + RWG)

        """
        Loss(t)=(B(t)-AT_min) * (Pen(t) / (AT_max-AT_min))
        """
        if B > AT_min:
            Loss_t = sheet_simulation.loc[t, "Loss(t)"] = (B - AT_min) * (
                pen / (AT_max - AT_min)
            )
        else:
            Loss_t = 0

        """
        PR(t) = Max{Min[Pen(t)-Loss(t),Pen(t)],0}
        """
        PR = sheet_simulation.loc[t, "PR(t)"] = max(min((pen - Loss_t), pen), 0)

        """
        func3: I(t) = B(t-1) / LE(t-1) + PR(t)
        """
        if t > 0:
            I = sheet_simulation.loc[t, "I(t)"] = (
                sheet_simulation.loc[t - 1, "B"]
                / sheet_simulation.loc[t - 1, "LE_t (years)"]
                + PR
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
        func1: w(t) =  ( I(t) / P(t) )** (1-ρ) / (1 - ρ)  -K1
        """
        ρ = sheet_simulation.loc[t, "ρ"] = ρ

        if t > 0:
            w = sheet_simulation.loc[t, "w"] = ((I / P) ** (1 - ρ)) / (1 - ρ) - K1

        # check passing
        if t > 0:
            W += w
            sheet_simulation.loc[t, "W"] = W
            if random.random() < life_expectancy_sheet.loc[t, "Prob_t"]:
                # passing
                """
                func8: Y(T) = K2 * ( B(T) / P(T) )**(1 - γ) / (1 - γ)
                """
                γ = sheet_simulation.loc[t, "γ"] = γ

                Y = sheet_simulation.loc[t, "Y"] = (
                    K2 * (B / P) ** (1 - γ) / (1 - γ)
                )  # Bequest well-being in year T
                W += Y

                sheet_simulation.loc[t, "W"] = W
                break

    sheet_simulation["I(t)/P"] = sheet_simulation["I(t)"] / sheet_simulation["P"]
    sheet_simulation["B/P"] = sheet_simulation["B"] / sheet_simulation["P"]

    json_data = sheet_simulation.to_json(orient="records")

    return JsonResponse(json_data, safe=False)
