import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import arviz as az

def visualise_player_specific():
    player_xgs = pd.read_csv('resources/player_effects_names.csv')
    stable_players = player_xgs[player_xgs["credible_width"] < 1.0]

    # convert from log odds to a multiplier i.e. 1 is baseline, 1.2 is 20% better
    stable_players["finishing_multiplier"] = np.exp(stable_players["mean"])

    top_10_players = stable_players.sort_values("mean", ascending=False).head(10)

    plt.figure(figsize = (12,8))
    plt.barh(top_10_players["player"], top_10_players["mean"])
    plt.gca().invert_yaxis()
    plt.title("Top 20 players (Log Odds Scale)")
    plt.xlabel("Player effect")
    plt.tight_layout()
    plt.savefig("resources/figures/player_specific/top_10_players.png", bbox_inches='tight')
    plt.show()

    plt.figure(figsize = (10,6))
    plt.errorbar(stable_players["mean"], range(len(stable_players)), xerr=[
        stable_players["mean"] - stable_players["eti89_lb"],
        stable_players["eti89_ub"] - stable_players["mean"]
    ], fmt="o")

    plt.title("Player Finishing Uncertainty")
    plt.xlabel("Effect size")
    plt.tight_layout()
    plt.savefig("resources/figures/player_specific/finishing_uncertainty.png", bbox_inches='tight')
    plt.show()

    plt.figure()
    plt.hist(stable_players["mean"], bins=30)
    plt.xlabel("theta_player mean")
    plt.savefig("resources/figures/player_specific/theta_player.png", bbox_inches='tight')
    plt.show()

    trace = az.from_netcdf("resources/model_trace.nc")

    az.plot_trace(trace, var_names=["beta_0", "beta_dist", "beta_angle", "sigma_player"])
    plt.savefig("resources/figures/player_specific/trace.png", bbox_inches='tight')
    plt.show()

    plt.figure(figsize = (10,6))
    plt.scatter(stable_players["mean"], stable_players["credible_width"])

    # label only the top 20 players
    for i, row in top_10_players.iterrows():
        plt.text(row["mean"], row["credible_width"], row["player"], fontsize=8)


    plt.xlabel("Finishing ability (theta_player mean)")
    plt.ylabel("Uncertainty (credible_width)")
    plt.title("Finishing Uncertainty vs player ability")
    plt.tight_layout()
    plt.savefig("resources/figures/player_specific/player_scatter.png", bbox_inches='tight')
    plt.show()
    
def visualise_basic_xg():
    shots_df = pd.read_csv('resources/shots_xg.csv')

    goals = shots_df[shots_df['goal'] == 1]
    non_goals = shots_df[shots_df['goal'] == 0]

    plt.figure()
    plt.hist(non_goals["xg"], bins=30, alpha=0.6, label="Non-goals")
    plt.hist(goals["xg"], bins=30, alpha=0.6, label="Goals")
    plt.xlabel("xg")
    plt.ylabel("count")
    plt.legend()
    plt.title("xG distribution for goals vs non-goals")
    plt.tight_layout()
    plt.savefig("resources/figures/base_xg/calaibration.png", bbox_inches='tight')
    plt.show()

    plt.figure()
    plt.scatter(shots_df["distance"], shots_df["xg"], alpha=0.3)
    plt.xlabel("Distance")
    plt.ylabel("xG")
    plt.title("Shot distance vs xG")
    plt.tight_layout()
    plt.savefig("resources/figures/base_xg/distance_xg.png", bbox_inches='tight')
    plt.show()

    plt.figure()
    plt.scatter(shots_df["angle"], shots_df["xg"], alpha=0.3)
    plt.xlabel("Angle")
    plt.ylabel("xG")
    plt.title("Shot angle vs xG")
    plt.tight_layout()
    plt.savefig("resources/figures/base_xg/angle_xg.png", bbox_inches='tight')
    plt.show()

    plt.figure()
    plt.scatter(shots_df["x"], shots_df["y"], c=shots_df["xg"], cmap='hot', alpha=0.6)
    plt.colorbar(label="xG")
    plt.title("Shot map coloured by xG")
    plt.xlabel("Pitch X")
    plt.ylabel("Pitch Y")
    plt.tight_layout()
    plt.savefig("resources/figures/base_xg/xg_heatmap.png", bbox_inches='tight')
    plt.show()