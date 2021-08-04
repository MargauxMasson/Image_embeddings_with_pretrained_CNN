# -*- coding: utf-8 -*-
"""Hub 2.0 Generate image embeddings using a pre-trained CNN and store them in Hub.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1eTtXTb-45Msfh9BZM4y7UUdj8cP-BQCI

# Generate image embeddings using a pre-trained CNN and store them in Hub
Author: Margaux Masson-Forsythe

## Imports
"""

!pip3 install hub==2.0.4 && torch==1.8.1
# restart runtime after installing
# using torch 1.8.1 because of an error 403 happening with the older version

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import hub
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import torch
from torchsummary import summary
import torchvision.models as models
import glob
from tqdm import tqdm
from PIL import Image

import matplotlib.pyplot as plt
# %matplotlib inline

print(hub.__version__)

print(torch.__version__)

"""## Load Data: Dog breeds from https://www.kaggle.com/eward96/dog-breed-images"""

!export KAGGLE_USERNAME="xxxx" && export KAGGLE_KEY="xxxxx" && mkdir -p data && cd data && kaggle datasets download -d eward96/dog-breed-images && unzip -n dog-breed-images.zip && rm dog-breed-images.zip

!ls data

data_dir = 'data'

list_imgs = glob.glob(data_dir + "/**/*.jpg")
print(f"There are {len(list_imgs)} images in the dataset {data_dir}")

# create dataloader with required transforms 
tc = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()              
    ])

image_datasets = datasets.ImageFolder(data_dir, transform=tc)
dloader = torch.utils.data.DataLoader(image_datasets, batch_size=10, shuffle=False)

for img, label in dloader:
  print(np.transpose(img[0], (1,2,0)).shape)
  print(img[0])
  plt.imshow((img[0].detach().numpy().transpose(1, 2, 0)*255).astype(np.uint8))
  plt.show()
  break

"""Pytorch default backend for images are Pillow, and when you use ToTensor()class, PyTorch automatically converts all images into [0,1] so no need to normalize the images here.

"""

len(image_datasets)

"""## Generate embeddings"""

def copy_embeddings(m, i, o):
    """Copy embeddings from the penultimate layer.
    """
    o = o[:, :, 0, 0].detach().numpy().tolist()
    outputs.append(o)

# fetch pretrained model
model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)

# Select the desired layer
layer = model._modules.get('avgpool')
# attach hook to the penulimate layer
_ = layer.register_forward_hook(copy_embeddings)

outputs = []  # list of embeddings

model.eval() # Inference mode

# Generate image's embeddings for all images in dloader and saves 
# them in the list outputs
for X, y in dloader:
    _ = model(X)

len(outputs)

# flatten list of embeddings to remove batches
list_embeddings = [item for sublist in outputs for item in sublist]
print(len(list_embeddings))

assert len(list_embeddings) == len(image_datasets)

np.array(list_embeddings[0]).shape

"""## Send to Hub"""

!activeloop login -u username -p password

hub_dogs_path = 'hub://margauxmforsythe/dogs_breeds_embeddings'

with hub.empty(hub_dogs_path) as ds:
    # Create the tensors 
    ds.create_tensor('images', htype = 'image', sample_compression = 'jpeg')
    ds.create_tensor('embeddings')

    # Add arbitrary metadata - Optional
    ds.info.update(description = 'Dog breeds embeddings dataset')
    ds.images.info.update(camera_type = 'SLR')
    
    # Iterate through the images and their corresponding embeddings, and append them to hub dataset
    for i in tqdm(range(len(image_datasets))):
      img = image_datasets[i][0].detach().numpy().transpose(1, 2, 0)
      img = img * 255 # images are normalized
      img = img.astype(np.uint8)
      ds.images.append(img)  # Append to Hub Dataset
      ds.embeddings.append(list_embeddings[i]) # Append to Hub Dataset
                
# Long-term storage is updated at the end of the code block inside 'with'

"""Let's see the images in the dataset ds and their embeddings"""

def show_image_in_ds(ds, idx=1):
    image = ds.images[idx].numpy()
    embedding = ds.embeddings[idx].numpy()
    print("Image:")
    print(image.shape)
    plt.imshow(image)
    plt.show()
    print(embedding[0:10]) # show only 10 first values of the image embedding

for i in range(2):
    show_image_in_ds(ds, i)

"""## Check the dataset was correctly sent to Hub"""

ds_from_hub = hub.dataset(hub_dogs_path)
Image.fromarray(ds_from_hub.images[0].numpy())

for i in range(4):
    show_image_in_ds(ds_from_hub, i)
