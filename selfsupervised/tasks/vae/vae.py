import torch
import torch.nn as nn
from transformers import BertModel


# Variational Autoencoder with BERT for Text
class VariationalAutoencoder(nn.Module):
    def __init__(self, num_dim, cat_dims, bert_model="bert-base-uncased", latent_dim=16):
        super().__init__()

        # Numerical Features
        self.num_encoder = nn.Sequential(nn.Linear(num_dim, 32), nn.ReLU())

        # Categorical Features (Embeddings)
        self.cat_embeddings = nn.ModuleList([nn.Embedding(cat_dim, 8) for cat_dim in cat_dims])
        self.cat_encoder = nn.Sequential(nn.Linear(len(cat_dims) * 8, 32), nn.ReLU())

        # BERT for Text Features
        self.bert = BertModel.from_pretrained(bert_model)
        self.text_encoder = nn.Linear(768, 32)  # Reduce BERT output dim

        # Latent Space for VAE
        self.fc_mu = nn.Linear(96, latent_dim)  # Mean
        self.fc_logvar = nn.Linear(96, latent_dim)  # Log variance

        # Separate Decoder Networks for Each Feature Type
        # Decoder for Numerical Features
        self.num_decoder = nn.Sequential(
            nn.Linear(latent_dim, 32), nn.ReLU(),
            nn.Linear(32, num_dim)  # Output numerical features
        )

        # Decoder for Categorical Features
        self.cat_decoder = nn.Sequential(
            nn.Linear(latent_dim, 32), nn.ReLU(),
            nn.Linear(32, sum(cat_dims))  # Output categorical features
        )

        # Decoder for Text Features (BERT output)
        self.text_decoder = nn.Sequential(
            nn.Linear(latent_dim, 32), nn.ReLU(),
            nn.Linear(32, 768)  # Output BERT embedding size (768)
        )

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std  # Sampling with reparameterization trick

    def forward(self, num_x, cat_x, text_x):
        # Encode Features
        num_enc = self.num_encoder(num_x)
        cat_enc = torch.cat([emb(cat_x[:, i]) for i, emb in enumerate(self.cat_embeddings)], dim=1)
        cat_enc = self.cat_encoder(cat_enc)
        text_emb = self.bert(text_x).pooler_output  # Use CLS token embedding
        text_enc = self.text_encoder(text_emb)

        # Concatenate Encodings & Map to Latent Space
        fused = torch.cat([num_enc, cat_enc, text_enc], dim=1)
        mu, logvar = self.fc_mu(fused), self.fc_logvar(fused)
        z = self.reparameterize(mu, logvar)

        # Separate Decoding for Each Feature Type
        num_recon = self.num_decoder(z)  # Reconstructed numerical features
        cat_recon = self.cat_decoder(z)  # Reconstructed categorical features
        text_recon = self.text_decoder(z)  # Reconstructed text features (BERT embeddings)

        return num_recon, cat_recon, text_recon, mu, logvar
