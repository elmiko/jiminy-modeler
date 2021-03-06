import math
from pyspark.mllib.recommendation import ALS
from operator import itemgetter
import itertools
import time
import numpy as np


class Estimator:
    def __init__(self, data):
        self._data = data
        #std bootstrap proportions for the training, validation and testing
        self._sets = self._split([0.6, 0.2, 0.2])


    def _split(self, proportions):
        split = self._data.randomSplit(proportions)
        return {'training': split[0], 'validation': split[1], 'test': split[2]}

    def rmse(self, model):
        predictions = model.predictAll(self._sets['validation'].map(lambda x: (x[0], x[1])))
        predictions_rating = predictions.map(Estimator.group_ratings)
        validation_rating = self._sets['validation'].map(Estimator.group_ratings)
        joined = validation_rating.join(predictions_rating)
        return math.sqrt(joined.map(lambda x: (x[1][0] - x[1][1]) ** 2).mean())

    # return ((userId, movieId), rating)
    @staticmethod
    def group_ratings(x):
        return ((int(x[0]), int(x[1])), float(x[2]))

    def _train(self, rank, iterations, lambda_, seed):
        return ALS.train(ratings=self._sets['training'],
                         rank=rank, seed=seed,
                         lambda_=lambda_,
                         iterations=iterations)

    def run(self, ranks, lambdas, iterations):
        # create combinations of parameters to test
        rmses = []
        combos=[]
        sizings = [len(ranks), len(lambdas), len(iterations)]

        for parameters in itertools.product(ranks, lambdas, iterations):
            rank, lambda_, iteration = parameters

            print "Evaluating parameters: %s" % str(parameters)

            start_time = time.time()

            rmse = self.rmse(self._train(rank=rank, iterations=iteration, lambda_=lambda_, seed=42))

            elapsed_time = time.time() - start_time

            print "RMSE = %f (took %f seconds)" % (rmse, elapsed_time)

            rmses.append(rmse)
            combos.append(parameters)
            print combos
        print rmses
        maximum = min(enumerate(rmses), key=itemgetter(1))[0]
        print enumerate(rmses)
        print min(enumerate(rmses), key=itemgetter(1))
        print maximum
        optimal = combos[maximum]
        return {
            'rank': optimal[0],
            'lambda': optimal[1],
            'iteration': optimal[2]
        }


class Trainer:
    def __init__(self, data, rank, iterations, lambda_, seed):
        self._data = data
        self.rank = rank
        self.iterations = iterations
        self.lambda_ = lambda_
        self.seed = seed

    def train(self):
        return ALS.train(ratings=self._data,
                         rank=self.rank,
                         seed=self.seed,
                         lambda_=self.lambda_,
                         iterations=self.iterations)
