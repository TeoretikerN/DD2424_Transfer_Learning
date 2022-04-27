import os
import shutil
from random import shuffle

train_val_ratio = 0.8

data_path = "data/images" # Original image folder with both cats and dogs
train_path = "data/catdog/train" # Has to exist before running
val_path = "data/catdog/val" # Has to exist before running

# Get all file names and shuffle
onlyfiles = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]
shuffle(onlyfiles)
train_files = onlyfiles[:int(train_val_ratio * len(onlyfiles))]
val_files = onlyfiles[int(train_val_ratio * len(onlyfiles)):]

# Move to train and val folders
for f in train_files:
	new_path = train_path
	new_path += "/cats" if f[0].isupper() else "/dogs"
	shutil.move(data_path + "/" + f, new_path + "/" + f)

for f in val_files:
	new_path = val_path
	new_path += "/cats" if f[0].isupper() else "/dogs"
	shutil.move(data_path + "/" + f, new_path + "/" + f)
