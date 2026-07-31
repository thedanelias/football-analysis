import data_setup, base_xg, player_xg, visualisations, evaluation

if __name__ == "__main__":
    data_setup.setup_data()
    base_xg.run_basic_model()
    player_xg.start_model()
    visualisations.visualise_basic_xg()
    visualisations.visualise_player_specific()
    evaluation.evaluate()