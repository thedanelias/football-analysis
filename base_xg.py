import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

def setup(shots_df):
    # categorise shot distance and angle / goal for ml
    x = shots_df[['distance', 'angle']]
    y = shots_df['goal']

    return x, y

def basic_model(x, y, shots_df):
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    model = LogisticRegression()
    model.fit(x_train, y_train)
    shots_df['xg'] = model.predict_proba(x)[:, 1]

    return model, x_test, y_test, shots_df

def evaluate(model, x_test, y_test, shots_df):
    print(shots_df[['distance', 'angle', 'goal', 'xg']].head())

    predictions = model.predict_proba(x_test)[:, 1]
    print(log_loss(y_test, predictions))
    print(roc_auc_score(y_test, predictions))

    print("Actual goals:", shots_df['goal'].sum())
    print("Expected goals:", shots_df['xg'].sum())


def run_basic_model():
    shots_df = pd.read_csv("resources/shots.csv")
    x, y = setup(shots_df)
    model, x_test, y_test, xg_df = basic_model(x, y, shots_df)
    evaluate(model, x_test, y_test, shots_df)
    xg_df.to_csv("resources/shots_xg.csv", index=False)
