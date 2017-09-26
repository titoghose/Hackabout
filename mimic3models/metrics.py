import numpy as np
from sklearn import metrics


# for decompensation, in-hospital mortality

def print_metrics_binary(y_true, predictions):
    predictions = np.array(predictions)
    if (len(predictions.shape) == 1):
        predictions = np.stack([1-predictions, predictions]).transpose((1, 0))
    
    cf = metrics.confusion_matrix(y_true, predictions.argmax(axis=1))
    print "confusion matrix:"
    print cf
    cf = cf.astype(np.float32)
    
    acc = (cf[0][0] + cf[1][1]) / np.sum(cf)
    prec0 = cf[0][0] / (cf[0][0] + cf[1][0])
    prec1 = cf[1][1] / (cf[1][1] + cf[0][1])
    rec0 = cf[0][0] / (cf[0][0] + cf[0][1])
    rec1 = cf[1][1] / (cf[1][1] + cf[1][0])
    auroc = metrics.roc_auc_score(y_true, predictions[:, 1])
    
    (precisions, recalls, thresholds) = metrics.precision_recall_curve(y_true, predictions[:, 1])
    auprc = metrics.auc(recalls, precisions)
    minpse = np.max([min(x, y) for (x, y) in zip(precisions, recalls)])
    
    print "accuracy =", acc
    print "precision class 0 =", prec0
    print "precision class 1 =", prec1
    print "recall class 0 =", rec0
    print "recall calss 1 =", rec1
    print "AUC of ROC =", auroc
    print "AUC of PRC =", auprc
    print "min(+P, Se) =", minpse
    
    return {"acc": acc,
            "prec0": prec0,
            "prec1": prec1,
            "rec0": rec0,
            "rec1": rec1,
            "auroc": auroc,
            "auprc": auprc,
            "minpse": minpse}


# for phenotyping

def print_metrics_multilabel(y_true, predictions):
    y_true = np.array(y_true)
    predictions = np.array(predictions)
    
    ave_prec_micro = metrics.precision_score(y_true > 0.5, predictions > 0.5,
                                                     average="micro")
    ave_prec_macro = metrics.precision_score(y_true > 0.5, predictions > 0.5,
                                                     average="macro")                                                 
    ave_prec_weighted = metrics.precision_score(y_true > 0.5, predictions > 0.5,
                                                     average="weighted")    
    
    ave_recall_micro = metrics.recall_score(y_true > 0.5, predictions > 0.5,
                                                     average="micro")
    ave_recall_macro = metrics.recall_score(y_true > 0.5, predictions > 0.5,
                                                     average="macro")                                                 
    ave_recall_weighted = metrics.recall_score(y_true > 0.5, predictions > 0.5,
                                                     average="weighted")    
    
    auc_scores = metrics.roc_auc_score(y_true, predictions, average=None)
    ave_auc_micro = metrics.roc_auc_score(y_true, predictions,
                                             average="micro")
    ave_auc_macro = metrics.roc_auc_score(y_true, predictions,
                                             average="macro")
    ave_auc_weighted = metrics.roc_auc_score(y_true, predictions,
                                             average="weighted")
    
    """
    print "ave_prec_micro =", ave_prec_micro
    print "ave_prec_macro =", ave_prec_macro
    print "ave_prec_weighted =", ave_prec_weighted
    print "-------------------------"

    print "ave_recall_micro =", ave_recall_micro
    print "ave_recall_macro =", ave_recall_macro
    print "ave_recall_weighted =", ave_recall_weighted
    print "-------------------------"
    """
    
    print "ROC AUC scores for labels:", auc_scores
    print "ave_auc_micro =", ave_auc_micro
    print "ave_auc_macro =", ave_auc_macro
    print "ave_auc_weighted =", ave_auc_weighted

    return {"ave_prec_micro": ave_prec_micro,
            "ave_prec_macro": ave_prec_macro,
            "ave_prec_weighted": ave_prec_weighted,
            "ave_recall_micro": ave_recall_micro,
            "ave_recall_macro": ave_recall_macro,
            "ave_recall_weighted": ave_recall_weighted,
            "auc_scores": auc_scores,
            "ave_auc_micro": ave_auc_micro,
            "ave_auc_macro": ave_auc_macro,
            "ave_auc_weighted": ave_auc_weighted}
            

# for length of stay

def mean_absolute_percentage_error(y_true, y_pred): 
    return np.mean(np.abs((y_true - y_pred) / (y_true + 0.1))) * 100


def print_metrics_regression(y_true, predictions):
    predictions = np.array(predictions)
    predictions = np.maximum(predictions, 0)
    y_true = np.array(y_true)

    y_true_bins = [get_bin_custom(x, CustomBins.nbins) for x in y_true]
    prediction_bins = [get_bin_custom(x, CustomBins.nbins) for x in predictions]
    cf = metrics.confusion_matrix(y_true_bins, prediction_bins)
    print "Custom bins confusion matrix:"
    print cf

    kappa = metrics.cohen_kappa_score(y_true_bins, prediction_bins,
                                      weights='linear')
    mad = metrics.mean_absolute_error(y_true, predictions)
    mse = metrics.mean_squared_error(y_true, predictions)
    mape = mean_absolute_percentage_error(y_true, predictions)

    print "Mean absolute deviation (MAD) =", mad
    print "Mean squared error (MSE) =", mse
    print "Mean absolute percentage error (MAPE) =", mape
    print "Cohen kappa score =", kappa

    return {"mad": mad,
            "mse": mse,
            "mape": mape,
            "kappa": kappa}


class LogBins:
    nbins = 10
    means = [0.611848, 2.587614, 6.977417, 16.465430, 37.053745, 
             81.816438, 182.303159, 393.334856, 810.964040, 1715.702848]

    
def get_bin_log(x, nbins, one_hot=False):
    binid = int(np.log(x + 1) / 8.0 * nbins)
    if (binid < 0):
        binid = 0
    if (binid >= nbins):
        binid = nbins - 1
    
    if one_hot:
        ret = np.zeros((LogBins.nbins,))
        ret[binid] = 1
        return ret
    return binid


# TODO: think about fix print_metrics_log_bins and print_metrics_custom_bins

def get_estimate_log(prediction, nbins):
    binid = np.argmax(prediction)
    return LogBins.means[binid]


def print_metrics_log_bins(y_true, predictions):
    y_true_bins = [get_bin_log(x, LogBins.nbins) for x in y_true]
    prediction_bins = [get_bin_log(x, LogBins.nbins) for x in predictions]
    cf = metrics.confusion_matrix(y_true_bins, prediction_bins)
    print "LogBins confusion matrix:"
    print cf
    return print_metrics_regression(y_true, predictions)


class CustomBins:
    inf = 1e18
    bins = [(-inf, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 14), (14, +inf)]
    nbins = len(bins)
    means = [11.450379, 35.070846, 59.206531, 83.382723, 107.487817,
            131.579534, 155.643957, 179.660558, 254.306624, 585.325890]


def get_bin_custom(x, nbins, one_hot=False):
    for i in range(nbins):
        a = CustomBins.bins[i][0] * 24.0
        b = CustomBins.bins[i][1] * 24.0
        if (x >= a and x < b):
            if one_hot:
                ret = np.zeros((CustomBins.nbins,))
                ret[i] = 1
                return ret
            return i
    return None


def get_estimate_custom(prediction, nbins):
    binid = np.argmax(prediction)
    assert binid >= 0 and binid < nbins
    return CustomBins.means[binid]


def print_metrics_custom_bins(y_true, predictions):
    return print_metrics_regression(y_true, predictions)