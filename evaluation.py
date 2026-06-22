import numpy as np
import pandas as pd
import arviz as az
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss, roc_auc_score, brier_score_loss
import matplotlib.pyplot as plt


def extract_player_xg(df, trace_path="resources/model_trace.nc"):
    df['player_code'] = pd.factorize(df['player_id'])[0]

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[['distance', 'angle']])
    distance = scaled_features[:, 0]
    angle = scaled_features[:, 1]

    trace = az.from_netcdf(trace_path)
    post = trace.posterior

    b0 = float(post['beta_0'].mean())
    b_dist = float(post['beta_dist'].mean())
    b_angle = float(post['beta_angle'].mean())

    theta_player_means = post['theta_player'].mean(dim=['chain', 'draw']).values
    codes = df['player_code'].values
    logit_p = b0 + (b_dist * distance) + (b_angle * angle) + theta_player_means[codes]

    perfect_probabilities = trace.posterior['xg_probabilities'].mean(dim=['chain', 'draw']).values
    df['player_xg'] = perfect_probabilities

    df.to_csv("resources/shots_player_xg.csv", index=False)
    return df

def compare_models():
    df = pd.read_csv("resources/shots_xg.csv")
    x = df[['distance', 'angle']]
    y = df['goal']
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    base_model = LogisticRegression()
    base_model.fit(x_train, y_train)

    df['base_xg'] = base_model.predict_proba(x)[:, 1]

    df = extract_player_xg(df)

    test_indices = x_test.index
    y_test_2 = df.loc[test_indices, 'goal']
    base_model_probs = df.loc[test_indices, 'base_xg']
    player_test_probs = df.loc[test_indices, 'player_xg']

    with open("resources/model_comparison.txt", "w") as f:
        message = f"""
        === MODEL PERFORMANCE COMPARISON (TEST SET) ===
        Baseline Log Loss:   {log_loss(y_test_2, base_model_probs):.4f}
        Player Log Loss:     {log_loss(y_test_2, player_test_probs):.4f}
        -----------------------------------------------
        Baseline ROC-AUC:    {roc_auc_score(y_test_2, base_model_probs):.4f}
        Player ROC-AUC:      {roc_auc_score(y_test_2, player_test_probs):.4f}
        -----------------------------------------------
        Baseline Brier Score: {brier_score_loss(df['goal'], df['base_xg']):.4f}
        Player Brier Score:   {brier_score_loss(df['goal'], df['player_xg']):.4f}
        
        === TOTALS CALIBRATION (FULL DATASET) ===
        Actual Total Goals: {df['goal'].sum()}
        Baseline Expected:  {df['base_xg'].sum():.1f}
        Player Expected:    {df['player_xg'].sum():.1f}
        """
        # save results to file and print it
        print(message)
        f.write(message)

def plot_best_finisher():
    df = pd.read_csv("resources/shots_player_xg.csv")
    df['xg_diff'] = df['player_xg'] - df['base_xg']

    best_player = df.groupby('player')['xg_diff'].mean().idxmax()
    best_player_df = df[df['player'] == best_player]

    print("The best finisher identified is: " + best_player)
    print(f"Total shots analysed for given player: {len(best_player_df)}")

    plt.figure()
    plt.scatter(best_player_df['base_xg'], best_player_df['player_xg'], alpha=0.7, label=f'{best_player}\'s Shots')
    plt.plot([0, 1], [0, 1], color='red', linestyle='--', linewidth=2, label='Average Finisher')

    plt.title(f"Base xG vs Personalised xG\nBest Finisher: {best_player}")
    plt.xlabel("Baseline Expected Goals (base_xg")
    plt.ylabel("Player-Adjusted Expected Goals (player_xg)")

    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig("resources/figures/player_specific/best_finisher_xg.png")
    plt.show()

def plot_top20_finishers():
    df = pd.read_csv("resources/shots_player_xg.csv")
    df['xg_diff'] = df['player_xg'] - df['base_xg']

    top_20_players = df.groupby('player')['xg_diff'].mean().nlargest(20).index.tolist()

    top_20_shots = df[df['player'].isin(top_20_players)]
    print("Top 20 finishers:")
    for i, player in enumerate(top_20_players, 1):
        print(f"{i}. {player}")
    print(f"Total shots analysed for given players: {len(top_20_shots)}")

    plt.figure()
    plt.scatter(top_20_shots['base_xg'], top_20_shots['player_xg'], alpha=0.7, label=f"Top 20 Finishers' Shots")
    plt.plot([0, 1], [0, 1], color='red', linestyle='--', linewidth=2, label='Average Finisher')

    plt.title("Base xG vs Personalised xG\nTop 20 Finishers")
    plt.xlabel("Baseline Expected Goals (base_xg")
    plt.ylabel("Player-Adjusted Expected Goals (player_xg)")

    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig("resources/figures/player_specific/top_20_xg.png")
    plt.show()

def evaluate():
    compare_models()
    plot_best_finisher()
    plot_top20_finishers()