# -*- coding: utf-8 -*-
"""frutas2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n9UCI17ItLU3ZT2isL3okHDq9WThRm8w

Es necesario instalar para poder importar desde Kaggle el dataset necesario
"""

!pip install -U kaggle

"""Kaggle nos brinda un json como clave para poder acceder a sus recursos"""

from google.colab import files
files.upload()

!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/

# This permissions change avoids a warning on Kaggle tool startup.
!chmod 600 ~/.kaggle/kaggle.json

"""Descargamos el dataset que necesitamos y lo descomprimimos"""

!kaggle datasets download -d chrisfilo/fruit-recognition

!unzip -q fruit-recognition.zip -d .

"""Importamos todas las librerías que creemos necesarias"""

import sys
import os 
import cv2
import random
import time
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
import keras

import numpy as np
from keras import layers
from keras.layers import Input, Dense, Activation, ZeroPadding2D, BatchNormalization, Flatten, Conv2D
from keras.layers import AveragePooling2D, MaxPooling2D, Dropout, GlobalMaxPooling2D, GlobalAveragePooling2D
from keras.models import Model,Sequential
from keras.preprocessing import image
from keras.utils import layer_utils
from keras.utils.data_utils import get_file
from keras.applications.imagenet_utils import preprocess_input
from keras.preprocessing.image import ImageDataGenerator
import pydot
from IPython.display import SVG
from keras.utils.vis_utils import model_to_dot
from keras.utils import plot_model,to_categorical


import keras.backend as K
import matplotlib.pyplot as plt
from matplotlib.pyplot import imshow

import pandas as pd
from  pathlib import Path
import random
from os import listdir
import re
from  pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
import os
import uuid
import json
import pandas as pd
import tensorflow as tf
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels

listdir()

"""Nos ubicamos en la carpeta en donde se encuentran las imágenes"""

!cd /content

#bool(re.search("[.|_]", "abcdefghijkl"))

"""convertimos las carpetas necesarias en un dataframe, el cual particionamos en train y test generando un random cada iteración(90% de probabilidad de ser train, 10% test), manipulando un poco las rutas y con la suerte de que todos los archivos están en formato png"""

dir=[]
fruit_dir= Path('.')
carpetas=['/content/Apple/Total Number of Apples','/content/Banana', '/content/Carambola', '/content/Guava/guava total final', 
          '/content/Kiwi/Total Number of Kiwi fruit', '/content/Mango', '/content/Pear', '/content/Orange']

          


for i in range(len(carpetas)):
  dir.append(fruit_dir / carpetas[i])
  print(i, end=" ")
print("")
datos=[]

for j in range(len(carpetas)):
  datos.append(dir[j].glob('*.png'))
  print(j, end=" ")
print("")
print(len(datos))
data=[]
splits=[]
f=0
cont=0
for k in datos:  
  for l in k:
    
    split=random.random()
    if split <0.9:
      spl='train'
      data.append((l,f))
      splits.append(spl)
      if cont<5:
        print(f, end= " ")
        cont+= 1
    else:
      spl='test'
      data.append((l,f))
      splits.append(spl)
  f+=1
print("")
df=pd.DataFrame()
df['names'],df['label']=zip(*data)

df['split']=splits
df = df.sample(frac=1).reset_index(drop=True)
print(len(df))
print(df['label'].unique())
df.head(20)

bar=plt.bar(['Train','Test'],df['split'].value_counts()[0:2])
bar[1].set_color('navy')

img=image.load_img(df['names'][16])
new_img = img. resize((256,256))
imshow(new_img)
df['names'][16]

img.mode

df_meta=df.copy()
df_meta.to_csv('meta_data.csv', index=False)
df=pd.read_csv('meta_data.csv')
#df=df.drop(['Unnamed: 0'],axis=1)
df.head(50)

"""**mostramos la cantidad de datos que tenemos por cada dato**"""

df.groupby('label').count()

"""Construimos las fuentes desde el metadata:"""

def build_sources_from_metadata(metadata, data_dir, mode='train'):  


    df = metadata.copy()
    df = df[df['split'] == mode]
    df['filepath'] = df['names'].apply(lambda x: os.path.join(data_dir, x))


    sources = list(zip(df['filepath'], df['label']))
    return sources

train_sources = build_sources_from_metadata(df, '.')
test_sources = build_sources_from_metadata(df, '.',mode='test')

(test_sources)[0]

"""*   make_dataset:Función para crear el dataset desde las fuentes:
      se crea un dataset de tensores y usamos varias funciones  
      de TF como  repeat batch y prefetch para aumentar, de ser  
      necesario el  rendimiento del algoritmo
      
*   load: función para cargar imágenes
*   preprocess_image: función para ajustar el tamaño de la imagen
*   imshow_batch_: función para mostrar imágenes por lotes
"""

def make_dataset(sources, batch_size=1,
    num_epochs=1, num_parallel_calls=1, shuffle_buffer_size=None, pixels = 224, target = 1):

    def load(row):
        filepath = row['image']
        img = tf.io.read_file(filepath)
        img = tf.io.decode_jpeg(img)
        return img, row['label']

    
    shuffle_buffer_size = batch_size*4

    images, labels = zip(*sources)
    
    ds = tf.data.Dataset.from_tensor_slices({
        'image': list(images), 'label': list(labels)}) 

    
    
    ds = ds.map(load, num_parallel_calls=num_parallel_calls)
    ds = ds.map(lambda x,y: (preprocess_image(x, pixels), y))
    
    
  
        
    #ds = ds.map(lambda x, y: (x, tuple([y]*target) if target > 1 else y))
    ds = ds.repeat(count=num_epochs)
    ds = ds.batch(batch_size=batch_size)
    ds = ds.prefetch(1)

    return ds

def preprocess_image(image,siz):
  image = tf.image.resize(image, size=(siz,siz))
  image = image / 255.0
  return image


def imshow_batch_(batch, show_label=True,cant=3):
    label_batch = batch[1].numpy()
    image_batch = batch[0].numpy()
    fig, axarr = plt.subplots(1, cant, figsize=(15, 5), sharey=True)
    for i in range(cant):
        img = image_batch[i, ...]
        axarr[i].imshow(img)
        if show_label:
            axarr[i].set(xlabel='label = {}'.format(label_batch[i]))

"""Crear dataset y mostrar batchs de imagenes"""

dataset = make_dataset(train_sources,batch_size=6, num_epochs=20,num_parallel_calls=1,pixels=224)

(dataset )

dataset = iter(dataset)
imshow_batch_(next(dataset),cant=6)

"""Función para la creación de una red neuronal estandar
empezando con una capa convolucional y agregando capas según los elementos en el parametro que es un vector. Si el elemento ingresado es 0 se entenderá que se debe hacer un maxpooling si el elemento ingresado es -1 se entenderá que se debe hacer un batchnormalization, de  otra manera se hará una convolución con tantos filtros como diga el elemento

De manera parecida se efectuará con el Dense Layer
si el elemento es 0 se efecturaá un Dropout, si es diferente se hará un Dense con tantas unidades como diga el elemento 

El último paso es un Dense con softmax y con el número de clases que tenemos.
 
---
"""

def build_standard_cnn(
    num_filters_per_convolutional_layer,
    num_units_per_dense_layer,
    input_shape,
    num_classes,
    activation='relu'):
    """
    """
    model = tf.keras.Sequential()
    model.add(
        tf.keras.layers.Conv2D(
            filters=num_filters_per_convolutional_layer[0],
            kernel_size=(3, 3), activation=activation,
            padding='same', input_shape=input_shape)
        )
    
    for num_filters in num_filters_per_convolutional_layer[1:]:
        
        if num_filters==0:
            model.add(tf.keras.layers.MaxPooling2D(pool_size=(2,2), strides=(2,2)))
        elif num_filters==-1:
            model.add(tf.keras.layers.BatchNormalization())        
        else:
            model.add(
                tf.keras.layers.Conv2D(
                    filters=num_filters,
                    kernel_size=(3, 3), activation=activation,
                    padding='same')
            )
        
    model.add(tf.keras.layers.Flatten())
    for num_units in num_units_per_dense_layer:
        if num_units==0:
            model.add(tf.keras.layers.Dropout(0.4))
        else:
            model.add(tf.keras.layers.Dense(num_units, activation=activation))
        
    model.add(tf.keras.layers.Dense(num_classes, activation='softmax'))
    
    return model

tf.keras.backend.clear_session()
CNN=build_standard_cnn([32,32,0,64,64,0,128,0],[1000,0,1000,0],(224,224,3),8)

"""RESUMEN"""

CNN.summary()

"""COmpilamos el modelo con el metodo de SparseCategoricalCrossentropy  que calculará la pérdida de la CrossEntropy entre las etiquetas y las predicciones. Usaremos el algoritmo Adam con parámetro 0,001 para optimizar el modelo"""

batch_size=32
epochs=5
lr=0.001

CNN.compile(loss=tf.losses.SparseCategoricalCrossentropy(),
            optimizer=tf.optimizers.Adam(lr),
            metrics=['accuracy'])

"""En la anterior celda le dimos un valor por default al batch size y escogimos 5 épocas.  Ahora creamos un dataset para train y uno para validación"""

train_dataset = make_dataset(train_sources,
    batch_size=batch_size, num_epochs=epochs,
    num_parallel_calls=5,pixels=224)

valid_dataset = make_dataset(test_sources,
    batch_size=batch_size, num_epochs=epochs,
    num_parallel_calls=5,pixels=224)

"""Entrenamos el modelo con duración aproximada de 50 minutos, parametros x= dataset de entrenamiento , 5 épocas y para el argumento validation_data usamos el dataset de validación"""

h=CNN.fit(x=train_dataset, epochs=5,validation_data=valid_dataset)

"""Imprimimos la gráficas de la pérdida y el  accuracy entre el train y el test"""

plt.figure(figsize=(15,4))
plt.subplot(1,2,1)
plt.ylim((0, 1))
plt.plot(h.history['loss'],label='train')
plt.plot(h.history['val_loss'],label='test')
plt.title('Loss')
plt.legend()
plt.subplot(1,2,2)
plt.ylim((0, 1))
plt.plot(h.history['accuracy'],label='train')
plt.plot(h.history['val_accuracy'],label='test')
plt.title('Accuracy')
plt.legend()

# Commented out IPython magic to ensure Python compatibility.
# %cd /content

CNN.save('model.h5')

CNN = keras.models.load_model('model.h5')

"""Creamos otro dataset con diferente tamaño de batch para poder crear la matriz de confusión, usamos predict_classes a este nuevo data_set."""

test_dataset= make_dataset(test_sources,
    batch_size=1, num_epochs=1,
    num_parallel_calls=5,pixels=224)

predict_classes=CNN.predict_classes(test_dataset)

"""cm = es la matriz de confusión no normalizada, para poder saber el número de clases bien predichas, solo se usan las etiquetas que aparecen en los datos y luego graficamos la matriz de una forma mucho más amigable"""

def plot_confusion_matrix(y_true, y_pred, classes,size,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues):

    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Confusion matrix, without normalization'

    # Compute confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    # Only use the labels that appear in the data
    classes = classes[unique_labels(y_true, y_pred)]
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)
    target_names=['Apples','Banana','Carambola','Guava','Kiwi','Mango','Pear','Organge']

    fig, ax = plt.subplots(figsize=(size,size))
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           xticklabels=target_names, yticklabels=target_names,
           title=title,
           ylabel='True label',
           xlabel='Predicted label')

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    return ax
  
import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels
a=np.array([0,1,2,3,4,5,6,7])

plot_confusion_matrix(df[df['split']=='test'].label,predict_classes,a,size=5)

"""Esta función nos permite mostrar lotes de imagenes y sus predicciones,  recibe un batch que contendrá las imagenes y los labels, con las imagenes predicirá el label usando el modelo y nos mostrará la imagen, su label y su predicción"""

def imshow_with_predictions(model, batch, show_label=True):    
    image_batch = batch[0].numpy()
    label_batch = batch[1].numpy()
    pred_batch = model.predict(image_batch)
    fig, axarr = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for i in range(3):
        img = image_batch[i, ...]
        axarr[i].imshow(img)
        pred = int(np.argmax(pred_batch[i]))
        msg = f'pred = {pred}'
        if show_label:
            msg += f', label = {label_batch[i]}'
        axarr[i].set(xlabel=msg)

"""la función anterior la probaremos con el valid_dataset y con el modelo CNN que fue el entrenado"""

v=iter(valid_dataset)

imshow_with_predictions(CNN, next(v))

"""Predicción incorrecta"""

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

imshow_with_predictions(CNN, next(v))

"""Calculamos, precision recall y f1-score y accuracy, vemos que el modelo se comporta de  buena manera"""

from sklearn.metrics import classification_report
target_names=['Apples','Banana','Carambola','Guava','Kiwi','Mango','Pear','Organge']
print(classification_report(df[df['split']=='test'].label,predict_classes, target_names=target_names))

"""DE aquí en adelante se creará un dataframe con las frutas que no fueron usadas en el modelo para probar que predice el modelo con datos fuera de contexto, esta  parte es identica a la extracción del dataframe al principio"""

dir=[]
fruit_dir= Path('.')
carpetas2=['/content/Persimmon','/content/Peach', '/content/Pitaya', '/content/Plum', 
          '/content/Pomegranate', '/content/Tomatoes', '/content/muskmelon']
          
target_c_names=target_names+['Persimon','Peach','Pitaya','Plum','Pomegranate','Tomatoes','Muskmelon']

for i in range(len(carpetas2)):
  dir.append(fruit_dir / carpetas2[i])

datos=[]

for j in range(len(carpetas2)):
  datos.append(dir[j].glob('*.png'))

data=[]
f=8
cont=0
for k in datos:  
  for l in k:
    data.append((l,f))
   
  f+=1

df2=pd.DataFrame()
df2['names'],df2['label']=zip(*data)


df2 = df2.sample(frac=1).reset_index(drop=True)

df2.head(20)

target_c_names=target_names+['Persimon','Peach','Pitaya','Plum','Pomegranate','Tomatoes','Muskmelon']
target_c_names

"""Se usan las funciones descritas anteriormente"""

def build_sources_from_metadata_fixed(metadata, data_dir, mode='train'):  


    df = metadata.copy()    
    df['filepath'] = df['names'].apply(lambda x: os.path.join(data_dir, x))


    sources = list(zip(df['filepath'], df['label']))
    return sources

"""creamos un dataset 'crazy' que solo obtendrá imágenes erróneas, para ver cómo se comporta el modelo"""

crazy_source=build_sources_from_metadata_fixed(df2,'.')

crazy_test=make_dataset(crazy_source,
    batch_size=batch_size, num_epochs=epochs,
    num_parallel_calls=5,pixels=224)

"""arreglamos un poco esta función para poder revisar correctamente los labels"""

def imshow_with_predictions_fixed(model, batch, show_label=True,target_c_names=['Apples','Banana',
                                                                                'Carambola','Guava','Kiwi','Mango',
                                                                                'Pear','Organge','Persimon','Peach',
                                                                                'Pitaya','Plum','Pomegranate','Tomatoes'
                                                                                ,'Muskmelon']):
    label_batch = batch[1].numpy()
    
    image_batch = batch[0].numpy()
    pred_batch = model.predict(image_batch)
    fig, axarr = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for i in range(3):
        img = image_batch[i, ...]
        axarr[i].imshow(img)
        pred = int(np.argmax(pred_batch[i]))
        msg = f'pred = {pred} '
        
        if show_label:
            msg += f', label = {label_batch[i]}'
        axarr[i].set(xlabel=msg)

"""E iteramos, en lotes de a 3"""

c=iter(crazy_test)

imshow_with_predictions_fixed(CNN, next(c))

imshow_with_predictions_fixed(CNN, next(c))

imshow_with_predictions_fixed(CNN, next(c))

imshow_with_predictions_fixed(CNN, next(c))

imshow_with_predictions_fixed(CNN, next(c))