import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from sklearn.preprocessing import StandardScaler


def player_setup(df):
    # map player ids starting from 0 i.e. no uuids
    player_codes, unique_players = pd.factorize(df['player_id'])
    df['player_code'] = player_codes
    return df, unique_players

def get_arrays(df):
    #scale distance and angle so they are standardised
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[['distance', 'angle']])
    distance_data = scaled_features[:, 0]
    angle_data = scaled_features[:, 1]

    goal_data = df['goal'].values
    player_codes = df['player_code'].values
    return distance_data, angle_data, goal_data, player_codes

def start_model():
    df = pd.read_csv('resources/shots.csv')
    shots_data, unique_players = player_setup(df)
    distance_data, angle_data, goal_data, codes = get_arrays(shots_data)
    num_players = len(unique_players)

    with pm.Model() as model:

        # contextual shot quality (fixed effects)
        beta_0 = pm.Normal('beta_0', -1, 1)
        beta_dist = pm.Normal('beta_dist', mu=0.0, sigma=1.0)
        beta_angle = pm.Normal('beta_angle', mu=0.0, sigma=1.0)

        # mean finishing ability
        mu_player = pm.Normal('mu_player', mu=0.0, sigma=1.0)

        # finishing ability (random effects)
        sigma_player = pm.Exponential('sigma_player', lam=1.0)

        # non-centred parameterisation to fix warnings (still gives same results but allows better sampling)
        z_player = pm.Normal('z_player', mu=0.0, sigma=1.0, shape=num_players)

        # player-specific
        theta_player_raw = mu_player + z_player * sigma_player
        theta_player = pm.Deterministic('theta_player', theta_player_raw - pm.math.mean(theta_player_raw))

        # follow the formula
        logit_p = beta_0 + (beta_dist * distance_data) + (beta_angle * angle_data) + theta_player[codes]

        pm.Deterministic('xg_probabilities', pm.math.invlogit(logit_p))

        # same as inverse-logit function
        goals = pm.Bernoulli('goals', logit_p=logit_p, observed=goal_data)

        with model:
            trace = pm.sample(draws=2000, tune=2000, chains=4, cores=4, target_accept=0.9, return_inferencedata=True, random_seed=42)
            pm.sample_posterior_predictive(trace, extend_inferencedata=True)
            trace.to_netcdf('resources/model_trace.nc')

        global_summary = az.summary(trace, var_names=['beta_0', 'beta_dist', 'beta_angle', 'mu_player', 'sigma_player'])
        global_summary.to_csv('resources/player_xg_summary.csv', index=False)
        player_summary = az.summary(trace, var_names=['theta_player']).reset_index()
        player_summary['player_code'] = player_summary['index'].str.extract(r'\[(\d+)\]').astype(int)

        # remove over-interpreted results
        player_summary["credible_width"] = (player_summary["eti89_ub"].astype(float) - player_summary["eti89_lb"].astype(float))
        id_name_map = shots_data[['player_code', 'player']].drop_duplicates(subset=['player_code'])
        merged_results = player_summary.merge(id_name_map, on='player_code', how='left')
        merged_results.to_csv("resources/player_effects_names.csv", index=False)



