import os
import argparse
import numpy as np
import pandas as pd
import random
random.seed(49297)


parser = argparse.ArgumentParser(description="Create data for length of stay prediction task.")
parser.add_argument('root_path', type=str, help="Path to root folder containing train and test sets.")
parser.add_argument('output_path', type=str, help="Directory where the created data should be stored.")
args, _ = parser.parse_known_args()

if not os.path.exists(args.output_path):
    os.makedirs(args.output_path)


def process_partition(partition, sample_rate=1.0, shortest_length=4.0, eps=1e-6):
    output_dir = os.path.join(args.output_path, partition)
    if (not os.path.exists(output_dir)):
        os.mkdir(output_dir)
    
    xty_triples = []
    patients = filter(str.isdigit, os.listdir(os.path.join(args.root_path, partition)))
    for (patient_index, patient) in enumerate(patients):
        patient_folder = os.path.join(args.root_path, partition, patient)
        patient_ts_files = filter(lambda x: x.find("timeseries") != -1, os.listdir(patient_folder))
        
        for ts_filename in patient_ts_files:
            with open(os.path.join(patient_folder, ts_filename)) as tsfile:
                lb_filename = ts_filename.replace("_timeseries", "")
                label_df = pd.read_csv(os.path.join(patient_folder, lb_filename))
            
                # empty label file 
                if (label_df.shape[0] == 0):
                    print "\n\t(empty label file)", patient, ts_filename
                    continue

                los = 24.0 * label_df.iloc[0]['Length of Stay'] # in hours
                if (pd.isnull(los)):
                    print "\n\t(length of stay is missing)", patient, ts_filename
                    continue
                
                ts_lines = tsfile.readlines()
                header = ts_lines[0]
                ts_lines = ts_lines[1:]
                event_times = [float(line.split(',')[0]) for line in ts_lines]
                
                ts_lines = [line for (line, t) in zip(ts_lines, event_times)
                                     if (t > -eps and t < los + eps)]
                event_times = [t for t in event_times 
                                     if (t > -eps and t < los + eps)]
                
                # no measurements in ICU
                if (len(ts_lines) == 0):
                    print "\n\t(no events in ICU) ", patient, ts_filename
                    continue
                
                sample_times = np.arange(0.0, los + eps, sample_rate)
                
                sample_times = filter(lambda x: x > shortest_length, sample_times)
                
                # At least one measurement
                sample_times = filter(lambda x: x > event_times[0], sample_times)
                
                output_ts_filename = patient + "_" + ts_filename
                with open(os.path.join(output_dir, output_ts_filename), "w") as outfile:
                    outfile.write(header)
                    for line in ts_lines:
                        outfile.write(line)
                
                for t in sample_times:
                    xty_triples.append((output_ts_filename, t, los - t))
                
        if ((patient_index + 1) % 100 == 0):
            print "\rprocessed %d / %d patients" % (patient_index + 1, len(patients)),

    print len(xty_triples)
    if partition == "train":
        random.shuffle(xty_triples)
    if partition == "test":
        xty_triples = sorted(xty_triples)

    with open(os.path.join(output_dir, "listfile.csv"), "w") as listfile:
        for (x, t, y) in xty_triples:
            listfile.write("%s,%.6f,%.6f\n" % (x, t, y))


process_partition("test")
process_partition("train")
