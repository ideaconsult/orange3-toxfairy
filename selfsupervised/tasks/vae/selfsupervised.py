import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from transformers import BertModel, BertTokenizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tasks.vae import VariationalAutoencoder
import os.path


# + tags=["parameters"]
upstream = ["vae_prepare"]  # Add upstream dependencies if needed
product = None
nepoch = None
# -

numeric_file = upstream["vae_prepare"]["numeric_file"]
categorical_file = upstream["vae_prepare"]["categorical_file"]
text_file = upstream["vae_prepare"]["text_file"]

if numeric_file is None and categorical_file is None and text_file is None:
    # Simulated Mixed Tabular Data (Replace with real dataset)
    np.random.seed(42)
    nrecords = 1000
    num_features = np.random.rand(nrecords, 3).astype(np.float32)  # 3 numerical
    cat_features = np.random.randint(0, 5, (nrecords, 2))  # 2 categorical (5 classes each)
    text_features = ["example sentence " + str(i) for i in range(nrecords)]  # Simulated text

    # Introduce Missing Values
    num_features[np.random.rand(*num_features.shape) < 0.2] = np.nan
    cat_features[np.random.rand(*cat_features.shape) < 0.2] = -1  # Categorical missing as -1
    text_features = ["" if np.random.rand() < 0.2 else text for text in text_features]  # Missing text as ""

    num_tensor = torch.tensor(num_features)
    cat_tensor = torch.tensor(cat_features, dtype=torch.long)
else:
    # Load data from files
    numeric_df = pd.read_csv(numeric_file)
    categorical_df = pd.read_csv(categorical_file)
    text_df = pd.read_csv(text_file)

    # Handle missing values (replace with NaN)
    numeric_df = numeric_df.replace([-np.inf, np.inf], np.nan)
    categorical_df = categorical_df.replace([-np.inf, np.inf], np.nan)

    # Standardize numerical data
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_df.values)
    num_tensor = torch.tensor(numeric_scaled, dtype=torch.float32)

    # Handle categorical data (replace NaN with -1)
    cat_features = categorical_df.fillna(-1).values
    cat_tensor = torch.tensor(cat_features, dtype=torch.long)

    # Handle text data
    text_features = text_df['text'].tolist()  # Assuming your text column is named 'text'



# Load BERT Tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Tokenize Text Features
text_tokens = tokenizer(text_features, padding=True, truncation=True, return_tensors="pt")
text_input_ids = text_tokens["input_ids"]
text_attention_mask = text_tokens["attention_mask"]

# Convert to Tensors

text_tensor = text_input_ids
text_mask = (text_tensor == 0)

# Replace NaNs/Missing Values with Default
num_tensor[torch.isnan(num_tensor)] = 0
cat_tensor[cat_tensor == -1] = 0

# Get BERT embeddings
bert_model = BertModel.from_pretrained("bert-base-uncased")
with torch.no_grad():
    bert_embeddings = bert_model(text_input_ids, attention_mask=text_attention_mask).pooler_output

# Split data into training and validation sets
num_train, num_val, cat_train, cat_val, text_train, text_val, bert_train, bert_val = train_test_split(
    num_tensor, cat_tensor, text_input_ids, bert_embeddings, test_size=0.2, random_state=42
)



def vae_loss(num_recon, cat_recon, text_recon, num_tensor, cat_tensor, bert_embeddings, mu, logvar, beta=0.1):
    # Numerical reconstruction loss (MSE)
    num_recon_loss = nn.MSELoss()(num_recon, num_tensor)

    # Categorical reconstruction loss (CrossEntropy)
    cat_dims = [5, 5]
    cat_recon_reshaped = cat_recon.view(-1, sum(cat_dims))
    cat_losses = []
    start_idx = 0
    for dim in cat_dims:
        end_idx = start_idx + dim
        cat_loss = nn.CrossEntropyLoss()(cat_recon_reshaped[:, start_idx:end_idx], cat_tensor[:, start_idx // 5])
        cat_losses.append(cat_loss)
        start_idx = end_idx
    cat_recon_loss = torch.mean(torch.stack(cat_losses))

    # Text reconstruction loss (MSE) - using bert_embeddings as target
    text_recon_loss = nn.MSELoss()(text_recon, bert_embeddings.float())

    # KL Divergence loss
    kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

    # Total loss: Reconstruction loss + KL divergence (with beta to control weight of KL)
    recon_loss = num_recon_loss + cat_recon_loss + text_recon_loss
    total_loss = recon_loss + beta * kl_loss

    return total_loss

# Model Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
cat_dims = [len(np.unique(cat_train[:, i].numpy())) for i in range(cat_train.shape[1])]
model = VariationalAutoencoder(num_dim=num_train.shape[1], cat_dims=cat_dims).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Check if model file exists and load it
model_path = product["model"]
if os.path.exists(model_path):
    print(f"Loading model from {model_path}")
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(torch.load(model_path, map_location=device)) # load the model state dict
    start_epoch = 0
    print ("Model loaded without optimizer or epoch data.")
else:
    print("Starting training from scratch.")
    start_epoch = 0

# Move Data to Device
num_train, cat_train, text_train, bert_train = num_train.to(device), cat_train.to(device), text_train.to(device), bert_train.to(device)
num_val, cat_val, text_val, bert_val = num_val.to(device), cat_val.to(device), text_val.to(device), bert_val.to(device)

# Training Loop
# Training and Validation Loop
for epoch in range(nepoch):
    model.train()  # Set model to training mode
    optimizer.zero_grad()

    # Training forward pass and loss calculation
    num_recon_train, cat_recon_train, text_recon_train, mu_train, logvar_train = model(num_train, cat_train, text_train)
    loss_train = vae_loss(num_recon_train, cat_recon_train, text_recon_train, num_train, cat_train, bert_train, mu_train, logvar_train)

    loss_train.backward()
    optimizer.step()

    # Validation
    model.eval()  # Set model to evaluation mode
    with torch.no_grad():
        num_recon_val, cat_recon_val, text_recon_val, mu_val, logvar_val = model(num_val, cat_val, text_val)
        loss_val = vae_loss(num_recon_val, cat_recon_val, text_recon_val, num_val, cat_val, bert_val, mu_val, logvar_val)

    if epoch % 10 == 0:
        print(f"Epoch [{epoch}/{nepoch}], Train Loss: {loss_train.item():.4f}, Val Loss: {loss_val.item():.4f}")


# Save the Model
torch.save(model.state_dict(), product["model"])
print("✅ Model weights saved!")

# Generate New Data from Latent Space
z_sample = torch.randn((5, 16)).to(device)
num_generated = model.num_decoder(z_sample).detach().cpu().numpy()
cat_generated = model.cat_decoder(z_sample).detach().cpu().numpy()
text_generated = model.text_decoder(z_sample).detach().cpu().numpy()

print("Generated Numerical Data Sample:\n", num_generated)
print("Generated Categorical Data Sample:\n", cat_generated)
print("Generated Text Data Sample:\n", text_generated)