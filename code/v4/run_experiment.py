from sklearn.feature_selection import *
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import *
from pathlib import Path
from base import * 
import argparse
import os

def run_experiment(experiment_type,parameters):
    return get_experiment(experiment_type)(**parameters)

def get_experiment(experiment_type):
    EXPERIMENTS = {
        'rfecv': rfecv_experiment,
        'select_percentile': select_percentile_experiment
    }
    if experiment_type not in EXPERIMENTS:
        raise ValueError(f"Invalid experiment type '{experiment_type}'")
    return EXPERIMENTS[experiment_type]


def rfecv_experiment(name=None, save_to='.', datasets=None, combine=False, label=None, models=None, scorer=None, save_best_model=False, cv=3, min_features_thresholds=[0.2,0.4,0.6,0.8,1.0]):
    # Set default name if not provided
    if name is None:
        name = generate_name()
    print(name)

    # Create experiment directory   
    experiment_dir = f"{save_to}/{name}"
    experiment_dir_results = f"{experiment_dir}/results"
    experiment_dir_best_models = f"{experiment_dir}/best_models"
    experiment_dir_checkpoint = f"{experiment_dir}/checkpoint.pkl"

    if Path(experiment_dir_checkpoint).exists():
        with open(experiment_dir_checkpoint, 'rb') as f:
            i_checkpoint, j_checkpoint, k_checkpoint = pickle.load(f)
        print(f'Continue from checkpoint = {(i_checkpoint, j_checkpoint, k_checkpoint)}')
    else:
        Path(experiment_dir).mkdir(parents=True, exist_ok=True)
        Path(experiment_dir_results).mkdir(parents=True, exist_ok=True)
        Path(experiment_dir_best_models).mkdir(parents=True, exist_ok=True)
        save_experiment(
            dict(name=name, save_to=experiment_dir, datasets=datasets, combine=combine, label=label, 
                    models=models, scorer=scorer, save_best_model=save_best_model, cv=cv, min_features_thresholds=min_features_thresholds),
            filepath= f'{experiment_dir}/experiment.yaml'
        )
        i_checkpoint, j_checkpoint, k_checkpoint = 0,0,0

    dataset_iterator = get_datasets(datasets, combine)     # Get dataset iterator
    y = get_dataset(label).values.flatten()     # Get label array
    model_list = get_models(models)     # Get list of models
    dataset_iterator = tqdm(dataset_iterator,total=31*len(model_list)*len(min_features_thresholds),initial = i_checkpoint*len(model_list)+j_checkpoint*len(min_features_thresholds)+k_checkpoint)
    for i,(dataset_name, dataset) in enumerate(dataset_iterator):
        if i < i_checkpoint:
            continue
        # Split data into train/test
        X_train, X_test, y_train, y_test = train_test_split(dataset, y, test_size=0.3, random_state=42)
        scaler = StandardScaler()
        X_train.loc[:] = scaler.fit_transform(X_train)
        X_test.loc[:] = scaler.fit_transform(X_test)
        # Loop over models
        for j,model in enumerate(model_list):
            # Loop over min features thresholds
            if i == i_checkpoint and j < j_checkpoint:
                continue

            features_thresholds = np.unique(np.ceil(np.array(min_features_thresholds) * len(dataset.columns))).astype(int) 
            features_bitmaps_seen = []
            for k,features_threshold in enumerate(features_thresholds):
                if i == i_checkpoint and j == j_checkpoint and k < k_checkpoint:
                    continue

                dataset_iterator.set_description(
                    f'{dataset_name=} ({i+1}), model={model.__class__.__name__} ({j+1}/{len(model_list)}), num_features={features_threshold}/{len(dataset.columns)} ({k+1}/{len(features_thresholds)})'
                )
                rfecv = RFECV(estimator=model, cv=cv, min_features_to_select=int(features_threshold*len(dataset.columns)))

                rfecv.fit(X_train, y_train)
                features_bitmaps = rfecv.ranking_ <= features_threshold
                if tuple(features_bitmaps) in features_bitmaps_seen:
                    pass
                else:
                    features_bitmaps_seen.append(tuple(features_bitmaps))
                    reduced_features = list(dataset.columns[features_bitmaps])                 # Get list of reduced features
                    # X_train_trf = rfecv.transform(X_train)                 # Get transformed training and testing data
                    # X_test_trf = rfecv.transform(X_test)
                    # print(rfecv.ranking_)
                    X_train_trf = X_train[reduced_features]
                    X_test_trf = X_test[reduced_features]
                    # Run test and get scores, predictions and model
                    scores, model, y_pred, fit_time = run_test(X_train_trf, X_test_trf, y_train, y_test, model, scorer)
                    # Write scores, reduced features, and fit time to file
                    features_threshold_str = str(features_threshold).replace('.', '_')
                    score_name,val = list(scores.items())[0]
                    score_str = '_'.join([score_name[:3],str(val).replace('.', '_')])
                    exp_str = i*len(model_list)*len(min_features_thresholds)+j*len(min_features_thresholds)+k
                    if exp_str < 10: exp_str = f'00{exp_str}'
                    elif exp_str < 100: exp_str = f'0{exp_str}'
                    else:
                        exp_str = f'{exp_str}'
                    filename = f"{experiment_dir_results}/{exp_str}_{score_str}_{dataset_name}_{model.__class__.__name__}_ft{len(reduced_features)}.txt"

                    with open(filename, 'w') as f:
                        f.write(f"Scores: {scores}\n")
                        f.write(f"Fit Time: {fit_time}\n")
                        f.write(f"Num Features: {len(reduced_features)}/{len(dataset.columns)}\n")
                        f.write(f"Features: {reduced_features}\n")
                    # Save best model if specified
                    if save_best_model:
                        save_model(model, f"{experiment_dir_best_models}/{dataset_name}_{model.__class__.__name__}_ft{sum(features_bitmaps)}.pkl")

                    del X_train_trf, X_test_trf, scores, y_pred, fit_time
                    gc.collect()

                dataset_iterator.update()
                with open(experiment_dir_checkpoint, 'wb') as f:
                    pickle.dump((i, j, k), f)



    if Path(experiment_dir_checkpoint).exists():
        os.remove(experiment_dir_checkpoint)


def select_percentile_experiment(name=None, save_to='.', datasets=None, combine=False, label=None, models=None, scorer=None, save_best_model=False, fs_scorer=None, fs_thresholds=[20,40,60,80,100]):
    # Set default name if not provided
    if name is None:
        name = generate_name()
    print(name)
    # Create experiment directory   
    experiment_dir = f"{save_to}/{name}"
    experiment_dir_results = f"{experiment_dir}/results"
    experiment_dir_best_models = f"{experiment_dir}/best_models"
    experiment_dir_checkpoint = f"{experiment_dir}/checkpoint.pkl"
    if Path(experiment_dir_checkpoint).exists():
        with open(experiment_dir_checkpoint, 'rb') as f:
            i_checkpoint, j_checkpoint, m_checkpoint, k_checkpoint = pickle.load(f)
        print(f'Continue from checkpoint = {(i_checkpoint, j_checkpoint,m_checkpoint, k_checkpoint)}')
    else:
        Path(experiment_dir).mkdir(parents=True, exist_ok=True)
        Path(experiment_dir_results).mkdir(parents=True, exist_ok=True)
        Path(experiment_dir_best_models).mkdir(parents=True, exist_ok=True)
        save_experiment(
            dict(name=name, save_to=experiment_dir, datasets=datasets, combine=combine, label=label, 
                    models=models, scorer=scorer, save_best_model=save_best_model, fs_thresholds=fs_thresholds),
            filepath= f'{experiment_dir}/experiment.yaml'
        )
        i_checkpoint, j_checkpoint, m_checkpoint, k_checkpoint = 0,0,0,0

    dataset_iterator = get_datasets(datasets, combine)     # Get dataset iterator
    y = get_dataset(label).values.flatten()     # Get label array
    model_list = get_models(models)     # Get list of models
    features_thresholds = np.unique(to_list(fs_thresholds)).astype(int) 
    i_len = None
    j_len = len(to_list(features_thresholds))
    m_len = len(to_list(fs_scorer))
    k_len = len(to_list(model_list))
    resume_pos = i_checkpoint*j_len+j_checkpoint*m_len + m_checkpoint*k_len+k_checkpoint
    dataset_iterator = tqdm(dataset_iterator,initial = resume_pos)

    for i,(dataset_name, dataset) in enumerate(dataset_iterator):
        if i < i_checkpoint:
            continue
        # Split data into train/test
        X_train, X_test, y_train, y_test = train_test_split(dataset, y, test_size=0.3, random_state=42)
        scaler = StandardScaler()
        X_train.loc[:] = scaler.fit_transform(X_train)
        X_test.loc[:] = scaler.fit_transform(X_test)

        features_bitmaps_seen = []
        for j,pctl_threshold in enumerate(features_thresholds):
            if i == i_checkpoint  and j < j_checkpoint:
                continue
            
            fs_scorers = [get_attr_from_module(fs_scorer_str,'sklearn.feature_selection') for fs_scorer_str in to_list(fs_scorer)]
            for m,fs_scorer_func in enumerate(fs_scorers):
                if i == i_checkpoint and j == j_checkpoint and m < m_checkpoint:
                    continue
            
                fea_selection = SelectPercentile(fs_scorer_func,percentile=pctl_threshold)
                fea_selection.fit(X_train, y_train)
                features_bitmaps = fea_selection.get_support()
                if tuple(features_bitmaps) in features_bitmaps_seen:
                    dataset_iterator.update(k_len)
                    pass
                else:
                    features_bitmaps_seen.append(tuple(features_bitmaps))
                    reduced_features = list(dataset.columns[features_bitmaps])                 # Get list of reduced features
                    X_train_trf = X_train[reduced_features]
                    X_test_trf = X_test[reduced_features]

                    for k,model in enumerate(model_list):
                        # Loop over min features thresholds
                        if i == i_checkpoint and j == j_checkpoint and m == m_checkpoint and k < k_checkpoint:
                            continue

                        dataset_iterator.set_description(
                            f'{dataset_name=} ({i+1})' +
                            f'model={model.__class__.__name__} ({k+1}/{len(model_list)}),' +
                            f'fs_scorer_func={fs_scorer_func.__name__} ({m+1}/{len(fs_scorer)})'
                            f'num_features={pctl_threshold}/{len(dataset.columns)} ({j+1}/{len(features_thresholds)})'
                        )

                        # Run test and get scores, predictions and model
                        scores, model, y_pred, fit_time = run_test(X_train_trf, X_test_trf, y_train, y_test, model, scorer)
                        # Write scores, reduced features, and fit time to file
                        features_threshold_str = str(pctl_threshold).replace('.', '_')
                        score_name,val = list(scores.items())[0]
                        score_str = '_'.join([score_name[:3],str(val).replace('.', '_')])


                        exp_str = dataset_iterator.n
                        if exp_str < 10: exp_str = f'00{exp_str}'
                        elif exp_str < 100: exp_str = f'0{exp_str}'
                        else: exp_str = f'{exp_str}'

                        filename = f"{experiment_dir_results}/{exp_str}_{score_str}_{dataset_name}_{model.__class__.__name__}_ft{len(reduced_features)}_{len(dataset.columns)}.txt"

                        with open(filename, 'w') as f:
                            f.write(f"Scores: {scores}\n")
                            f.write(f"Fit Time: {fit_time}\n")
                            f.write(f"Num Features: {len(reduced_features)}/{len(dataset.columns)}\n")
                            f.write(f"Features: {reduced_features}\n")
                        # Save best model if specified
                        if save_best_model:
                            save_model(model, f"{experiment_dir_best_models}/{dataset_name}_{model.__class__.__name__}_ft{len(reduced_features)}.pkl")
                        
                        dataset_iterator.update()

                    del X_train_trf, X_test_trf, scores, y_pred, fit_time
                    gc.collect()
                    
                with open(experiment_dir_checkpoint, 'wb') as f:
                    pickle.dump((i, j, m, k), f)



    if Path(experiment_dir_checkpoint).exists():
        os.remove(experiment_dir_checkpoint)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train a model on a dataset')
    parser.add_argument('--experiment_file', type=str, default='experiments.yaml', help='Experiment')
    args = parser.parse_args()

    experiments = load_experiment(args.experiment_file)
    for name,experiment_configs in experiments.items():
        run_experiment(**experiment_configs)
        print()

# cd code/v4 
# python3 run_experiment.py