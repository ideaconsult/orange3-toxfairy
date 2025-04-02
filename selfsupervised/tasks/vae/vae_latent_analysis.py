# latent_space_analysis.py

import torch
import numpy as np
import pandas as pd
from transformers import BertModel, BertTokenizer
from sklearn.preprocessing import StandardScaler
import umap
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from tasks.vae import VariationalAutoencoder  # Import the VAE model class

# + tags=["parameters"]
upstream = ["selfsupervised"]  # Add upstream dependencies if needed
product = None
numeric_file = None
categorical_file = None
text_file = None
labels_file = None
# -

def load_latent_space(model_path, numeric_file, categorical_file, text_file, device):
    """Loads a trained VAE model and returns the latent space."""
    numeric_df = pd.read_csv(numeric_file)
    categorical_df = pd.read_csv(categorical_file)
    text_df = pd.read_csv(text_file)
    numeric_df = numeric_df.replace([-np.inf, np.inf], np.nan)
    categorical_df = categorical_df.replace([-np.inf, np.inf], np.nan)
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_df.values)
    num_tensor = torch.tensor(numeric_scaled, dtype=torch.float32).to(device)
    cat_features = categorical_df.fillna(-1).values
    cat_tensor = torch.tensor(cat_features, dtype=torch.long).to(device)
    text_features = text_df['text'].tolist()
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    text_tokens = tokenizer(text_features, padding=True, truncation=True, return_tensors="pt")
    text_input_ids = text_tokens["input_ids"].to(device)
    text_attention_mask = text_tokens["attention_mask"].to(device)
    bert_model = BertModel.from_pretrained("bert-base-uncased").to(device)
    with torch.no_grad():
        bert_embeddings = bert_model(text_input_ids, attention_mask=text_attention_mask).pooler_output.to(device)

    cat_dims = [len(np.unique(cat_tensor[:, i].cpu().numpy())) for i in range(cat_tensor.shape[1])]
    model = VariationalAutoencoder(num_dim=num_tensor.shape[1], cat_dims=cat_dims).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    with torch.no_grad():
        _, _, _, mu, _ = model(num_tensor, cat_tensor, text_input_ids)

    return mu.cpu().numpy()

def visualize_latent_space(latent_space, labels=None):
    """Visualizes the latent space using UMAP."""
    reducer = umap.UMAP()
    embedding = reducer.fit_transform(latent_space)
    plt.figure(figsize=(10, 8))
    if labels is not None:
        plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='Spectral', s=5)
        plt.colorbar(label='Labels')
    else:
        plt.scatter(embedding[:, 0], embedding[:, 1], s=5)
    plt.title('UMAP of Latent Space')
    plt.xlabel('UMAP Dimension 1')
    plt.ylabel('UMAP Dimension 2')
    plt.show()

def build_supervised_model(latent_space, labels_file):
    """Builds a supervised classification model using the latent space."""
    labels_df = pd.read_csv(labels_file)
    labels = labels_df['label'].values  # Assuming your label column is named 'label'

    X_train, X_test, y_train, y_test = train_test_split(latent_space, labels, test_size=0.2, random_state=42)
    print(X_train)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Supervised Model Accuracy: {accuracy}")




np.random.seed(42)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

latent_space = load_latent_space(upstream["selfsupervised"]["model"], numeric_file, categorical_file, text_file, device)

df = pd.DataFrame(latent_space)
df.to_csv(product["latent"], index=False)

visualize_latent_space(latent_space, labels=pd.read_csv(labels_file)['label'].values)
build_supervised_model(latent_space, labels_file)    