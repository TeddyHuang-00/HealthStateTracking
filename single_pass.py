import pandas as pd

tracking = pd.read_csv("./data/tracking.csv")
tracking[tracking["健康码"] == "红码", "健康状态"] = "确诊"
tracking[(tracking["健康码"] == "黄码") & (tracking["健康状态"] == "健康"), "健康状态"] = "异常"
