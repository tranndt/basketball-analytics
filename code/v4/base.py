import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import gc
from sklearn.exceptions import * 
import warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from sklearn import (svm, linear_model, ensemble, dummy, tree,  
                     gaussian_process, neighbors,kernel_ridge, neural_network, multioutput,
                     cross_decomposition)

MODELS = {
    'ARDRegression': linear_model.ARDRegression,
    'AdaBoostRegressor': ensemble.AdaBoostRegressor,
    'BaggingRegressor': ensemble.BaggingRegressor,
    'BayesianRidge': linear_model.BayesianRidge,
    'DecisionTreeRegressor': tree.DecisionTreeRegressor,
    'DummyRegressor': dummy.DummyRegressor,
    'ElasticNet': linear_model.ElasticNet,
    'ElasticNetCV': linear_model.ElasticNetCV,
    'ExtraTreeRegressor': tree.ExtraTreeRegressor,
    'ExtraTreesRegressor': ensemble.ExtraTreesRegressor,
    'GaussianProcessRegressor': gaussian_process.GaussianProcessRegressor,
    'GradientBoostingRegressor': ensemble.GradientBoostingRegressor,
    'GradientBoostingClassifier': ensemble.GradientBoostingClassifier,
    'HuberRegressor': linear_model.HuberRegressor,
    'KNeighborsRegressor': neighbors.KNeighborsRegressor,
    'KNeighborsClassifier': neighbors.KNeighborsClassifier,
    'KernelRidge': kernel_ridge.KernelRidge,
    'Lars': linear_model.Lars,
    'LarsCV': linear_model.LarsCV,
    'Lasso': linear_model.Lasso,
    'LassoCV': linear_model.LassoCV,
    'LassoLars': linear_model.LassoLars,
    'LassoLarsCV': linear_model.LassoLarsCV,
    'LassoLarsIC': linear_model.LassoLarsIC,
    'LinearRegression': linear_model.LinearRegression,
    'LinearSVR': svm.LinearSVR,
    'LogisticRegression': linear_model.LogisticRegression,
    'LogisticRegressionCV': linear_model.LogisticRegressionCV,
    'MLPRegressor': neural_network.MLPRegressor,
    'MultiOutputRegressor': multioutput.MultiOutputRegressor,
    'MultiTaskElasticNet': linear_model.MultiTaskElasticNet,
    'MultiTaskElasticNetCV': linear_model.MultiTaskElasticNetCV,
    'MultiTaskLasso': linear_model.MultiTaskLasso,
    'MultiTaskLassoCV': linear_model.MultiTaskLassoCV,
    'NuSVR': svm.NuSVR,
    'OrthogonalMatchingPursuit': linear_model.OrthogonalMatchingPursuit,
    'OrthogonalMatchingPursuitCV': linear_model.OrthogonalMatchingPursuitCV,
    'PLSCanonical': cross_decomposition.PLSCanonical,
    'PLSRegression': cross_decomposition.PLSRegression,
    'PassiveAggressiveRegressor': linear_model.PassiveAggressiveRegressor,
    'RANSACRegressor': linear_model.RANSACRegressor,
    'RadiusNeighborsRegressor': neighbors.RadiusNeighborsRegressor,
    'RandomForestClassifier': ensemble.RandomForestClassifier,
    'RandomForestRegressor': ensemble.RandomForestRegressor,
    'Ridge': linear_model.Ridge,
    'RidgeCV': linear_model.RidgeCV,
    'RidgeClassifier': linear_model.RidgeClassifier,
    'RidgeClassifierCV': linear_model.RidgeClassifierCV,
    'SGDRegressor': linear_model.SGDRegressor,
    'SVR': svm.SVR,
    'SVC': svm.SVC,
    'StackingRegressor': ensemble.StackingRegressor,
    'TheilSenRegressor': linear_model.TheilSenRegressor,
    'VotingRegressor': ensemble.VotingRegressor
}

def get_model(model_name, *args, **kwargs):
    if model_name not in MODELS:
        raise ValueError(f"Invalid model name '{model_name}'")
    model_class = MODELS[model_name]
    return model_class(*args, **kwargs)

def get_models(model_names,model_args=None,model_kwargs=None):
    models = []
    if model_args is None:
        model_args = []
    if model_kwargs is None:
        model_kwargs = []
    for i,model_name in enumerate(model_names):
        args = model_args[i] if i < len(model_args) else []
        kwargs = model_kwargs[i] if i < len(model_kwargs) else {}
        models.append(get_model(model_name, *args, **kwargs))
    return models

from itertools import combinations
from typing import Iterable, Union

def get_dataset(dataset_name:str,folder: str = './data/2000-2022/'):
    return pd.read_csv(f"{folder}{dataset_name}.csv").drop(columns='Unnamed: 0')

def get_datasets(dataset_names: Union[str, Iterable[str]], combine: bool = False, folder: str = './data/2000-2022/'):
    if isinstance(dataset_names, str):
        dataset_names = [dataset_names]
    
    dataframes = [get_dataset(dataset,folder=folder) for dataset in dataset_names]
    
    for dataset_name,dataframe in zip(dataset_names,dataframes):
        yield dataset_name,dataframe

    if combine:
        for i in range(2, len(dataset_names) + 1):
            for comb_dataset in combinations(dataset_names, i):
                comb_dataset_name = '|'.join(comb_dataset)
                comb_dataframe = [pd.read_csv(f"{folder}{dataset}.csv").drop(columns='Unnamed: 0') for dataset in comb_dataset]               
                comb_dataframe = pd.concat(comb_dataframe,axis=1,keys=comb_dataset)
                yield comb_dataset_name, comb_dataframe


import random
from datetime import datetime

def generate_name(prefix='',suffix=''):
    # List of fruit-related adjectives
    adjectives = ['juicy', 'ripe', 'sweet', 'tart', 'tasty', 'ripe', 'colorful', 'fragrant', 'succulent']
    # List of fruits
    fruits = ['apple', 'banana', 'orange', 'mango', 'kiwi', 'pineapple', 'papaya', 'pear', 'grape', 'lemon', 'lime']
    # Generate random adjective and fruit
    adjective = random.choice(adjectives)
    fruit = random.choice(fruits)
    # Generate datetime string in yymmdd-HHMM format
    now = datetime.now()
    dt_string = now.strftime("%y%m%d_%H%M%S")
    # Combine all parts to form name
    name = f"{prefix}{dt_string}_{adjective}_{fruit}{suffix}"
    return name

import pickle

def save_model(model, filename):
    with open(filename, 'wb') as f:
        pickle.dump(model, f)

def load_model(filename):
    with open(filename, 'rb') as f:
        model = pickle.load(f)
    return model

import yaml

def load_experiment(filepath):
    with open(filepath) as f:
        experiments = yaml.load(f, Loader=yaml.FullLoader)
    return experiments

def save_experiment(experiment,filepath):
    with open(filepath, 'w') as f:
        yaml.dump(experiment, f)

from sklearn.metrics import make_scorer

# def get_scorer(scorer_name):
#     try:
#         return getattr(__import__('sklearn.metrics', fromlist=[scorer_name]), scorer_name)
#     except AttributeError:
#         return make_scorer(scorer_name)

def get_attr_from_module(attr, module_name):
    import importlib
    import inspect

    module = importlib.import_module(module_name)
    try:
        return getattr(module, attr)
    except:
        for _, sub_module in inspect.getmembers(module, inspect.ismodule):
            try:
                return get_attr_from_module(attr, f"{module_name}.{sub_module.__name__}")
            except:
                pass
    return None
    
from typing import List, Union

import numpy as np
from sklearn.metrics import get_scorer
import time

def run_test(X_train, X_test, y_train, y_test, model, scorer: Union[callable, List[callable], str, List[str]], scorer_args: Union[List[dict], dict] = None) -> Union[float, List[float]]:
    # If the scorer is a single function, convert it to a list
    if callable(scorer) or isinstance(scorer,str):
        scorer = [scorer]

    for i,s in enumerate(scorer):
        if isinstance(s,str):
            scorer[i] = get_scorer(s)._score_func
    # If scorer_args is not a list, make it into a list with a single element
    if not isinstance(scorer_args, list):
        scorer_args = [scorer_args]
    
    start = time.time()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    fit_time = np.round(time.time() - start,3)

    scores = {}
    for i, score_func in enumerate(scorer):
        score_func_args = scorer_args[i] if i < len(scorer_args) and scorer_args[i] is not None else {}
        score = score_func(y_test,y_pred,**score_func_args)
        scores[score_func.__name__] = np.round(score,6)

    return scores, model, y_pred, fit_time

def to_list(var):
    if not isinstance(var, Iterable) or isinstance(var, str):
        return [var]
    else:
        return var