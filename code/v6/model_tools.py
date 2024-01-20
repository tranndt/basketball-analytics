
import pandas as pd
from sklearn.ensemble import AdaBoostClassifier, AdaBoostRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, RidgeClassifier
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.datasets import make_classification, make_regression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error, accuracy_score, f1_score, precision_score, recall_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.svm import SVC, SVR
from tqdm import tqdm
from file_tools import *
from datetime import datetime

class ModelStack:
    MODELS_CLASSIFICATION = {
        'RandomForestClassifier': RandomForestClassifier(),
        'LogisticRegression': LogisticRegression(),
        'RidgeClassifier': RidgeClassifier(),
        'SVC': SVC(),
        'MLPClassifier': MLPClassifier(),
        'KNeighborsClassifier': KNeighborsClassifier(),
        'AdaBoostClassifier': AdaBoostClassifier()
    }
    MODELS_REGRESSION = {
        'RandomForestRegressor': RandomForestRegressor(),
        'Ridge': Ridge(),
        'SVR': SVR(),
        'LinearRegression': LinearRegression(),
        'MLPRegressor': MLPRegressor(),
        # 'KNeighborsRegressor': KNeighborsRegressor(),
        'AdaBoostRegressor': AdaBoostRegressor()
    }
    MODEL_PARAMS_CLASSIFICATION = {
        'RandomForestClassifier': {'n_estimators': 100},
        'LogisticRegression': {'max_iter': 1000},
        'RidgeClassifier': {},
        'SVC': {},
        'MLPClassifier': {},
        'KNeighborsClassifier': {},
        'AdaBoostClassifier': {}
    }
    MODEL_PARAMS_REGRESSION = {
        'RandomForestRegressor': {'n_estimators': 100},
        'Ridge': {},
        'SVR': {},
        'LinearRegression': {},
        'MLPRegressor': {},
        # 'KNeighborsRegressor': {},
        'AdaBoostRegressor': {}
    }
    SCORES_CLASSIFICATION = ['accuracy','f1','precision','recall']
    SCORES_REGRESSION = ['mse','r2','mae','rmse']

    def __init__(self, models='classification', model_params='classification'):
        if models == 'classification':
            models = ModelStack.MODELS_CLASSIFICATION
            model_params = ModelStack.MODEL_PARAMS_CLASSIFICATION
        elif models == 'regression':
            models = ModelStack.MODELS_REGRESSION
            model_params = ModelStack.MODEL_PARAMS_REGRESSION
        elif isinstance(models, list):
            joined_models_dicts = ModelStack.MODELS_CLASSIFICATION.update(ModelStack.MODELS_REGRESSION)
            joined_model_params_dicts = ModelStack.MODEL_PARAMS_CLASSIFICATION.update(ModelStack.MODEL_PARAMS_REGRESSION)
            models = {k:v for k,v in joined_models_dicts.items() if k in models}
            model_params = {k:v for k,v in joined_model_params_dicts.items() if k in models}
            # scoring_funcs = [FeatureStack.SCORING_FUNCS_DICT[f] for f in scoring_funcs if f in FeatureStack.SCORING_FUNCS_DICT.keys()]

        self.models = models 
        self.model_params = model_params
        self.predictions = None
        self.scores = None
        self.__init_models__()

    def __init_models__(self):
        for model_name, model in self.models.items():
            model.set_params(**self.model_params[model_name])
            self.models[model_name] = model

    def fit_predict(self, X, y, scaler=None, **kwargs):
        X_train, X_val, y_train, y_val = train_test_split(X, y, **kwargs)
        train_predictions = pd.DataFrame(index=X_train.index)
        val_predictions = pd.DataFrame(index=X_val.index)
        if scaler is not None:
            X_train = scaler.fit_transform(X_train)
            X_val = scaler.transform(X_val)

        for model_name, model in self.models.items():
            fitted_model = model.fit(X_train, y_train)
            train_predictions[model_name] = fitted_model.predict(X_train)
            val_predictions[model_name] = fitted_model.predict(X_val)
        train_predictions.insert(0, 'y_true', y_train)
        val_predictions.insert(0, 'y_true', y_val)
        # Concatenating and adding labels
        predictions = pd.concat([train_predictions, val_predictions], keys=['train', 'val'])
        self.predictions = predictions
        return predictions
    
    def score(self, predictions, score_names='classification'):
        if score_names == 'classification':
            score_names = ModelStack.SCORES_CLASSIFICATION
        elif score_names == 'regression':
            score_names = ModelStack.SCORES_REGRESSION
        scores = {}
        for score_name in score_names:
            for model_name in self.models.keys():
                train_true = predictions.loc['train']['y_true']
                train_pred = predictions.loc['train'][model_name]
                val_true = predictions.loc['val']['y_true']
                val_pred = predictions.loc['val'][model_name]

                train_score = self._calculate_score(train_true, train_pred, score_name)
                val_score = self._calculate_score(val_true, val_pred, score_name)
                scores[(score_name,'train', model_name, )] = train_score
                scores[(score_name, 'val', model_name, )] = val_score

        scores = pd.Series(scores).unstack(level=[1,0]).sort_index(axis=1)
        self.scores = scores
        return scores
    
    @classmethod
    def score(cls,y_preds,y_true=None, score_names='classification'):
        if score_names == 'classification':
            score_names = ModelStack.SCORES_CLASSIFICATION
        elif score_names == 'regression':
            score_names = ModelStack.SCORES_REGRESSION
        elif isinstance(score_names, str):
            score_names = [score_names]
        elif isinstance(score_names, list):
            score_names = [score_name for score_name in score_names if score_name in ModelStack.SCORES_CLASSIFICATION + ModelStack.SCORES_REGRESSION]
            
        y_preds_ = y_preds.copy()
        if y_true is None:
            y_true = y_preds_.pop('y_true')
        scores = {}
        for model_name in y_preds.columns.drop('y_true'):
            for score_name in score_names:
                val_score = ModelStack._calculate_score(y_true, y_preds_[model_name], score_name)
                scores[(score_name, model_name)] = val_score
        scores = pd.Series(scores).unstack(level=[0]).sort_index(axis=1)
        return scores

    @classmethod
    def _calculate_score(cls,y_true, y_pred, score_name):
        # Classification metrics
        if score_name == 'accuracy':
            return accuracy_score(y_true, y_pred)
        elif score_name == 'f1':
            return f1_score(y_true, y_pred)
        elif score_name == 'precision':
            return precision_score(y_true, y_pred)
        elif score_name == 'recall':
            return recall_score(y_true, y_pred)
        
        # Regression metrics
        elif score_name == 'mse':
            return mean_squared_error(y_true, y_pred)
        elif score_name == 'r2':
            return r2_score(y_true, y_pred)
        elif score_name == 'mae':
            return mean_absolute_error(y_true, y_pred)
        elif score_name == 'rmse':
            return mean_squared_error(y_true, y_pred, squared=False)
        else:
            raise ValueError(f"Unknown score name: {score_name}")
        
    def get_params(self):
        params_dict = {}
        for model_name, model in self.models.items():
            params_dict[model_name] = (model.__class__.__name__, self.model_params[model_name])
        return params_dict
    

class ModelStackCV(ModelStack):
    """
    Sample Usage:
    -------------
    ```
    model_finder = ModelStackCV(ModelFinder.MODELS_CLASSIFICATION, ModelFinder.MODEL_PARAMS_CLASSIFICATION)
    X, y = make_classification(n_samples=1000, n_features=20, random_state=2)  # Example dataset
    predictions = model_finder.fit_predict(pd.DataFrame(X), pd.Series(y), cv=3)
    scores = model_finder.score(predictions, ModelFinder.SCORES_CLASSIFICATION)
    ```
    """
    def __init__(self, models='classification', model_params='classification'):
        super().__init__(models, model_params)

    def fit_predict(self, X, y, cv=3,scaler=None, **kwargs):
           
        predictions = pd.DataFrame()
        kf_predictions_dict = {}
        kf = KFold(n_splits=cv,**kwargs)
        for i, (train_index, val_index) in enumerate(kf.split(X)):
            X_train, X_val = X.iloc[train_index], X.iloc[val_index]
            y_train, y_val = y.iloc[train_index], y.iloc[val_index]

            kf_train_predictions = pd.DataFrame(index=X_train.index)
            kf_val_predictions = pd.DataFrame(index=X_val.index)
            if scaler is not None:
                X_train = scaler.fit_transform(X_train)
                X_val = scaler.transform(X_val)

            for model_name, model in self.models.items():
                fitted_model = model.fit(X_train, y_train)
                kf_train_predictions[model_name] = fitted_model.predict(X_train)
                kf_val_predictions[model_name] = fitted_model.predict(X_val)

            kf_train_predictions.insert(0, 'is_Val', 0)
            kf_val_predictions.insert(0, 'is_Val', 1)
            kf_predictions = pd.concat([kf_train_predictions, kf_val_predictions])
            kf_predictions_dict[i] = kf_predictions

        predictions = pd.concat(kf_predictions_dict.values(), keys=kf_predictions_dict.keys(),axis=1).reorder_levels([1,0],axis=1).sort_index(axis=1).sort_index(axis=0)
        predictions.insert(0, 'y_true', y)    
        self.predictions = predictions
        return predictions


    def score(self, predictions, score_names='classification', avg_cv=True):
        if score_names == 'classification':
            score_names = ModelStack.SCORES_CLASSIFICATION
        elif score_names == 'regression':
            score_names = ModelStack.SCORES_REGRESSION
        scores = {}
        for model_name in self.models.keys():
            for cv_fold in predictions[model_name].columns:
                is_val_fold = predictions['is_Val'][cv_fold]
                train_index_fold = is_val_fold[is_val_fold == 0].index
                val_index_fold = is_val_fold[is_val_fold == 1].index
                
                train_true_fold = predictions.loc[train_index_fold]['y_true']
                train_pred_fold = predictions.loc[train_index_fold][model_name][cv_fold]
                val_true_fold = predictions.loc[val_index_fold]['y_true']
                val_pred_fold = predictions.loc[val_index_fold][model_name][cv_fold]

                for score_name in score_names:
                    train_score_fold = self._calculate_score(train_true_fold, train_pred_fold, score_name)
                    val_score_fold = self._calculate_score(val_true_fold, val_pred_fold, score_name)
                    scores[( score_name,'train', model_name, cv_fold, )] = train_score_fold
                    scores[(score_name, 'val', model_name, cv_fold, )] = val_score_fold
        scores = pd.Series(scores)
        if avg_cv:
            scores = scores.groupby(level=[0,1,2]).mean().unstack(level=[1,0]).sort_index(axis=1)

        self.scores = scores
        return scores

    def run_experiment(
        self,
        X,
        y,
        cv,
        scaler,
        score_names,
        save_dir = None,
        experiment_name='experiment',
    ):
        if save_dir:
            experiment_name = datetime.now().strftime('%Y%m%d-%H%M%S')+f'-{experiment_name}'
            save_dir = os.path.join(save_dir,experiment_name)
            make_directory(save_dir)
        # If X and y are dictionaries, then run experiment for each key
        if isinstance(X,dict):
            predictions = {}
            scores = {}
            TQDM_X_ITEMS = tqdm(X.items(),ncols=150)
            for name,Xi in TQDM_X_ITEMS:
                TQDM_X_ITEMS.set_description(name)
                try:
                    yi = y[name] if isinstance(y,dict) else y
                    predictions[name] = self.fit_predict(Xi,yi,cv=cv,scaler=scaler)
                    scores[name] = self.score(predictions[name], score_names)
                    if save_dir:
                        pd.concat(predictions,axis=0).to_csv(os.path.join(save_dir,'predictions.csv'))
                        pd.concat(scores,axis=0).to_csv(os.path.join(save_dir,'scores.csv'))
                except Exception as e:
                    # Skipping any potential error when handling one of the dataframes
                    print(f'Skipped experiment for {name} due to: {e}')
                    continue
            predictions = pd.concat(predictions,axis=0)
            scores = pd.concat(scores,axis=0)

        # Else run experiment for the whole dataset
        else:
            predictions = self.fit_predict(X,y,cv=cv,scaler=scaler)
            scores = self.score(predictions, score_names)

        # Save Predictions
        if save_dir:
            predictions.to_csv(os.path.join(save_dir,'predictions.csv'))
            scores.to_csv(os.path.join(save_dir,'scores.csv'))
        return predictions, scores 

    
    
from sklearn.feature_selection import GenericUnivariateSelect, f_classif, f_regression, mutual_info_classif, mutual_info_regression, r_regression
import numpy as np

class FeatureStack:
    """
    Sample Usage:
    ------------
    ```
    feature_stack = FeatureStack([f_classif, mutual_info_classif], mode='k_best', params=[10, 15, 20])
    X, y = make_classification(n_samples=1000, n_features=30)  # Example dataset
    X, y = pd.DataFrame(X), pd.Series(y)
    feature_stack.fit(X, y)
    # Iterate through transformed datasets
    for transformed_X,meta in feature_stack.transform(X):
        print(meta, transformed_X.shape)
        # Do something with transformed_X
    ```
    """
    CLASSIFCATION_SCORING_FUNCS = [f_classif, mutual_info_classif, r_regression]
    REGRESSION_SCORING_FUNCS =  [f_regression, mutual_info_regression, r_regression]
    SCORING_FUNCS_DICT = {
        'f_classif': f_classif,
        'f_regression': f_regression,
        'mutual_info_classif': mutual_info_classif,
        'mutual_info_regression': mutual_info_regression,
        'r_regression': r_regression
    }

    def __init__(self, scoring_funcs, mode, params):
        if scoring_funcs == 'classification':
            scoring_funcs = FeatureStack.CLASSIFCATION_SCORING_FUNCS
        elif scoring_funcs == 'regression':
            scoring_funcs = FeatureStack.REGRESSION_SCORING_FUNCS
        elif isinstance(scoring_funcs, str) and scoring_funcs in FeatureStack.SCORING_FUNCS_DICT.keys():
            scoring_funcs = [FeatureStack.SCORING_FUNCS_DICT[scoring_funcs]]
        elif isinstance(scoring_funcs, list):
            scoring_funcs = [FeatureStack.SCORING_FUNCS_DICT[f] for f in scoring_funcs if f in FeatureStack.SCORING_FUNCS_DICT.keys()]

        self.scoring_funcs = scoring_funcs
        self.mode = mode
        self.params = params
        self.scores = None
        self.scores_ranked = None
        self.transformed_columns = {}

    def fit(self, X, y):
        scores = {}
        for score_func in self.scoring_funcs:
            transformer = GenericUnivariateSelect(score_func, mode=self.mode, param=0)
            transformer.fit(X, y)
            scores[score_func.__name__] = transformer.scores_

        self.scores = pd.DataFrame(scores, index=X.columns)
        self.scores_ranked = self.scores.abs().rank(method='min', ascending=False)

    def transform(self, X):
        for param in self.params:
            for score_func in self.scoring_funcs:
                yield self._transform_single(X, score_func.__name__, param),(score_func.__name__,self.mode,param)

    def _transform_single(self, X, score_func_name, param):
        if self.mode == 'k_best':
            selected_features = self.scores_ranked[score_func_name].nsmallest(param).index
        elif self.mode == 'percentile':
            threshold = np.percentile(self.scores_ranked[score_func_name], param)
            selected_features = self.scores_ranked[score_func_name][self.scores_ranked[score_func_name] <= threshold].index
        X_sel = X[selected_features]
        self.transformed_columns[(score_func_name,self.mode,param)] = selected_features
        return X_sel

